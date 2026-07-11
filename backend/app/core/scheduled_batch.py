"""Scheduled/manual batch orchestration.

Runs the MVP pipeline in one process:

1. Fetch/normalize public Polymarket market data, or read a normalized JSON file.
2. Store snapshots and compute metrics.
3. Detect expectation-shift signals for the same metric run.
4. Research, verify, and store bounded context candidates when configured.
5. Generate stored AI reports for qualifying issues.
6. Record one collection log for the combined run.

The public API remains read-only; this module is the explicit write path for
local/dev or scheduled batch execution.
"""

import argparse
import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.ai_report import LLMClient, build_openai_client
from app.core.ai_report_batch import (
    ReportOutcome,
    run_ai_report_batch,
    run_ai_report_batch_for_latest_metrics,
)
from app.core.collector import fetch_events
from app.core.config import settings
from app.core.context_research import (
    OpenRouterContextResearchClient,
    build_context_research_client_from_settings,
)
from app.core.context_research_batch import ContextResearchOutcome, run_context_research_batch
from app.core.context_verification import (
    IndependentVerifierClient,
    build_independent_verifier_from_settings,
)
from app.core.historical_seed import ensure_local_dev_write_allowed
from app.core.signal_detection import detect_signals_for_run
from app.core.snapshot_metrics import BatchRunResult, run_snapshot_and_metrics
from app.db.models import DataCollectionLog, MarketMetric

logger = logging.getLogger(__name__)

DEFAULT_NORMALIZED_PATH = Path(__file__).resolve().parents[3] / "normalized_samples.json"
DEFAULT_ARTIFACT_DIR = Path(__file__).resolve().parents[3] / "artifacts" / "scheduled_batch"


@dataclass
class ScheduledBatchResult:
    run_started_at: datetime
    run_finished_at: datetime | None = None
    run_timestamp: datetime | None = None
    reports_only: bool = False
    skipped_duplicate_run: bool = False
    normalized_count: int = 0
    markets_processed: int = 0
    markets_failed: int = 0
    signals_inserted: int = 0
    context_outcomes: list[ContextResearchOutcome] | None = None
    report_outcomes: list[ReportOutcome] | None = None
    error: str | None = None

    @property
    def reports_success(self) -> int:
        return sum(1 for outcome in self.report_outcomes or [] if outcome.status == "success")

    @property
    def reports_failed_or_filtered(self) -> int:
        return sum(
            1
            for outcome in self.report_outcomes or []
            if outcome.status in {"failed", "filtered"}
        )

    @property
    def reports_skipped(self) -> int:
        return sum(1 for outcome in self.report_outcomes or [] if outcome.status == "skipped")

    @property
    def context_success(self) -> int:
        return sum(
            1
            for outcome in self.context_outcomes or []
            if outcome.status in {"success", "no_candidate"}
        )

    @property
    def context_failed(self) -> int:
        return sum(1 for outcome in self.context_outcomes or [] if outcome.status == "failed")

    @property
    def context_candidates_accepted(self) -> int:
        return sum(outcome.accepted_count for outcome in self.context_outcomes or [])


def load_normalized_markets(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as fh:
        payload = json.load(fh)
    if not isinstance(payload, list):
        raise ValueError(f"Expected {path} to contain a list of normalized markets.")
    return [item for item in payload if isinstance(item, dict)]


def record_scheduled_batch_log(db: Session, result: ScheduledBatchResult) -> None:
    status = "success"
    if result.error:
        status = "failed"
    elif result.skipped_duplicate_run:
        status = "skipped_duplicate"
    elif result.markets_failed or result.context_failed or result.reports_failed_or_filtered:
        status = "partial"

    db.add(
        DataCollectionLog(
            run_started_at=result.run_started_at,
            run_finished_at=result.run_finished_at or datetime.now(UTC),
            status=f"scheduled_batch_{status}",
            markets_processed=result.markets_processed,
            markets_failed=result.markets_failed,
            error_detail={
                "reports_only": result.reports_only,
                "normalized_count": result.normalized_count,
                "run_timestamp": result.run_timestamp.isoformat()
                if result.run_timestamp
                else None,
                "signals_inserted": result.signals_inserted,
                "context_success": result.context_success,
                "context_failed": result.context_failed,
                "context_candidates_accepted": result.context_candidates_accepted,
                "reports_success": result.reports_success,
                "reports_failed_or_filtered": result.reports_failed_or_filtered,
                "reports_skipped": result.reports_skipped,
                "error": result.error,
            },
        )
    )
    db.commit()


def latest_metric_run(db: Session) -> datetime | None:
    return db.execute(select(func.max(MarketMetric.computed_at))).scalar_one_or_none()


def run_reports_for_timestamp(
    db: Session,
    run_timestamp: datetime,
    llm_client: LLMClient | None,
    model_name: str,
) -> list[ReportOutcome]:
    if llm_client is None:
        logger.info("Skipping AI reports: no LLM client configured.")
        return []
    return run_ai_report_batch(db, run_timestamp, llm_client, model_name)


def run_reports_for_current_db(
    db: Session,
    llm_client: LLMClient | None,
    model_name: str,
) -> list[ReportOutcome]:
    if llm_client is None:
        logger.info("Skipping AI reports: no LLM client configured.")
        return []
    return run_ai_report_batch_for_latest_metrics(db, llm_client, model_name)


def run_scheduled_batch(
    db: Session,
    *,
    normalized_markets: list[dict[str, Any]] | None = None,
    llm_client: LLMClient | None,
    model_name: str,
    context_research_client: OpenRouterContextResearchClient | None = None,
    context_verifier: IndependentVerifierClient | None = None,
    context_backfill: bool = False,
    reports_only: bool = False,
    record_log: bool = True,
) -> ScheduledBatchResult:
    result = ScheduledBatchResult(run_started_at=datetime.now(UTC), reports_only=reports_only)

    try:
        if reports_only:
            run_timestamp = latest_metric_run(db)
            if run_timestamp is None:
                raise RuntimeError("No market_metrics rows found for reports-only run.")
            result.run_timestamp = run_timestamp
        else:
            if normalized_markets is None:
                raise ValueError("normalized_markets is required unless reports_only=True.")
            result.normalized_count = len(normalized_markets)
            if not normalized_markets:
                raise RuntimeError("No normalized markets available for this batch run.")
            metric_result: BatchRunResult = run_snapshot_and_metrics(normalized_markets, db)
            result.skipped_duplicate_run = metric_result.skipped_duplicate_run
            result.run_timestamp = metric_result.run_timestamp
            result.markets_processed = metric_result.markets_processed
            result.markets_failed = metric_result.markets_failed
            if not result.skipped_duplicate_run:
                signals = detect_signals_for_run(db, metric_result.run_timestamp)
                result.signals_inserted = len(signals)

        if (
            context_research_client is not None
            and context_verifier is not None
            and result.run_timestamp is not None
            and not result.skipped_duplicate_run
        ):
            result.context_outcomes = run_context_research_batch(
                db,
                result.run_timestamp,
                context_research_client,
                context_verifier,
                use_latest_metrics=reports_only,
                backfill=context_backfill,
                change_threshold=settings.context_change_threshold,
                staleness=timedelta(hours=settings.context_staleness_hours),
                budget_usd=settings.context_budget_usd,
                cost_reservation_usd=settings.context_cost_reservation_usd,
            )
        else:
            result.context_outcomes = []

        if reports_only:
            result.report_outcomes = run_reports_for_current_db(
                db,
                llm_client,
                model_name,
            )
        elif not result.skipped_duplicate_run and result.run_timestamp is not None:
            result.report_outcomes = run_reports_for_timestamp(
                db,
                result.run_timestamp,
                llm_client,
                model_name,
            )
        else:
            result.report_outcomes = []

    except Exception as exc:
        db.rollback()
        result.error = f"{type(exc).__name__}: {exc}"
        logger.exception("Scheduled batch failed.")
    finally:
        result.run_finished_at = datetime.now(UTC)
        if record_log:
            try:
                record_scheduled_batch_log(db, result)
            except Exception:
                db.rollback()
                logger.exception("Failed to record scheduled batch log.")

    return result


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the Outlook Signals data/metric/signal/report batch."
    )
    source = parser.add_mutually_exclusive_group()
    source.add_argument(
        "--use-live-fetch",
        action="store_true",
        help="Fetch fresh Polymarket Gamma data before writing snapshots/metrics.",
    )
    source.add_argument(
        "--normalized-path",
        type=Path,
        default=None,
        help="Use a normalized JSON artifact instead of live fetch.",
    )
    parser.add_argument(
        "--reports-only",
        action="store_true",
        help="Generate AI reports from the latest existing metric run without collecting data.",
    )
    parser.add_argument("--max-samples", type=int, default=50)
    parser.add_argument("--fetch-limit", type=int, default=100)
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument(
        "--skip-ai-reports",
        action="store_true",
        help="Run data/metric/signal generation but skip AI report generation.",
    )
    parser.add_argument(
        "--skip-context-research",
        action="store_true",
        help="Run the existing batch without the optional v4 context stage.",
    )
    parser.add_argument(
        "--context-backfill",
        action="store_true",
        help="Research every latest eligible metric once; local/dev writes only.",
    )
    parser.add_argument(
        "--confirm-local-dev-write",
        action="store_true",
        help="Required before this command writes to the configured local/dev DB.",
    )
    return parser


def normalized_markets_from_args(args: argparse.Namespace) -> list[dict[str, Any]] | None:
    if args.reports_only:
        return None
    if args.use_live_fetch:
        args.artifact_dir.mkdir(parents=True, exist_ok=True)
        return fetch_events(
            limit=args.fetch_limit,
            max_samples=args.max_samples,
            output_dir=args.artifact_dir,
        )
    return load_normalized_markets(args.normalized_path or DEFAULT_NORMALIZED_PATH)


def ai_extra_headers_from_settings() -> dict[str, str]:
    headers: dict[str, str] = {}
    if settings.ai_provider == "openrouter":
        if settings.openrouter_http_referer:
            headers["HTTP-Referer"] = settings.openrouter_http_referer
        if settings.openrouter_app_title:
            headers["X-OpenRouter-Title"] = settings.openrouter_app_title
    return headers


def main() -> int:
    from app.db.session import get_session_factory

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    args = build_arg_parser().parse_args()

    ensure_local_dev_write_allowed(settings.env, args.confirm_local_dev_write)
    if not settings.database_url:
        raise SystemExit("DATABASE_URL is not set.")

    normalized_markets = normalized_markets_from_args(args)
    llm_client = None
    if not args.skip_ai_reports:
        if not settings.ai_api_key:
            raise SystemExit("OPENAI_API_KEY or OPENROUTER_API_KEY is not set.")
        llm_client = build_openai_client(
            settings.ai_api_key,
            settings.openai_model,
            base_url=settings.ai_base_url,
            provider_name=settings.ai_provider,
            extra_headers=ai_extra_headers_from_settings(),
        )

    context_research_client = None
    context_verifier = None
    if not args.skip_context_research:
        try:
            context_research_client = build_context_research_client_from_settings(settings)
            context_verifier = build_independent_verifier_from_settings(settings)
        except Exception as exc:
            logger.info("Skipping context research: %s", type(exc).__name__)

    session = get_session_factory()()
    try:
        result = run_scheduled_batch(
            session,
            normalized_markets=normalized_markets,
            llm_client=llm_client,
            model_name=settings.openai_model,
            context_research_client=context_research_client,
            context_verifier=context_verifier,
            context_backfill=args.context_backfill,
            reports_only=args.reports_only,
        )
    finally:
        session.close()

    logger.info(
        "Scheduled batch complete: processed=%s failed=%s signals=%s reports_success=%s "
        "context_success=%s context_failed=%s reports_skipped=%s error=%s",
        result.markets_processed,
        result.markets_failed,
        result.signals_inserted,
        result.reports_success,
        result.context_success,
        result.context_failed,
        result.reports_skipped,
        result.error,
    )
    return (
        1
        if result.error
        or result.markets_failed
        or result.context_failed
        or result.reports_failed_or_filtered
        else 0
    )


if __name__ == "__main__":
    raise SystemExit(main())
