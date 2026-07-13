"""Guarded local/development CLI for pending v8 generation requests."""

import argparse
import logging
from uuid import UUID

from app.core.ai_report import build_openai_client
from app.core.config import settings
from app.core.context_policy_v7 import build_v8_conditional_verifier_from_settings
from app.core.context_research import build_context_research_client_from_settings
from app.core.generation_runtime import ensure_generation_worker_allowed
from app.core.on_demand_briefing import (
    process_v8_request,
    refresh_v8_context_for_market,
    run_pending_v8_requests,
)
from app.core.scheduled_batch import ai_extra_headers_from_settings
from app.db.session import get_session_factory


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Process pending on-demand v8 briefings.")
    parser.add_argument("--max-requests", type=int, default=10)
    parser.add_argument(
        "--request-id",
        type=UUID,
        help="Process only this generation request instead of scanning the pending queue.",
    )
    parser.add_argument("--confirm-generation-write", action="store_true")
    return parser


def build_context_refresher():
    """Build a lazy bounded v8 context refresher for the worker process."""
    research_client = None
    verifier = None

    def refresh(db, market_id, now):
        nonlocal research_client, verifier
        if research_client is None:
            research_client = build_context_research_client_from_settings(settings)
            verifier = build_v8_conditional_verifier_from_settings(settings)
        refresh_v8_context_for_market(
            db,
            market_id,
            now,
            research_client=research_client,
            verifier=verifier,
            budget_usd=settings.context_budget_usd,
            cost_reservation_usd=settings.context_cost_reservation_usd,
        )

    return refresh


def main() -> int:
    args = build_arg_parser().parse_args()
    ensure_generation_worker_allowed(
        settings.env,
        args.confirm_generation_write,
        production_enabled=settings.generation_workers_enabled,
    )
    if not settings.database_url:
        raise SystemExit("DATABASE_URL is not set.")
    if not settings.ai_api_key:
        raise SystemExit("OPENAI_API_KEY or OPENROUTER_API_KEY is not set.")
    client = build_openai_client(
        settings.ai_api_key,
        settings.openai_model,
        base_url=settings.ai_base_url,
        provider_name=settings.ai_provider,
        extra_headers=ai_extra_headers_from_settings(),
    )
    context_refresher = build_context_refresher()
    session = get_session_factory()()
    try:
        if args.request_id is not None:
            result = process_v8_request(
                session,
                args.request_id,
                client,
                settings.openai_model,
                context_refresher=context_refresher,
            )
            if result.successor_request_id is not None:
                result = process_v8_request(
                    session,
                    result.successor_request_id,
                    client,
                    settings.openai_model,
                    context_refresher=context_refresher,
                )
            results = [result]
        else:
            results = run_pending_v8_requests(
                session,
                client,
                settings.openai_model,
                max_requests=min(max(args.max_requests, 1), 50),
                context_refresher=context_refresher,
            )
    finally:
        session.close()
    logging.info(
        "On-demand worker complete: attempted=%s succeeded=%s failed=%s",
        len(results),
        sum(result.state == "succeeded" for result in results),
        sum(result.state == "failed" for result in results),
    )
    return 1 if any(result.state == "failed" for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
