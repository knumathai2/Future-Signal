"""Guarded local/development CLI for pending v7 generation requests."""

import argparse
import logging

from app.core.ai_report import build_openai_client
from app.core.config import settings
from app.core.historical_seed import ensure_local_dev_write_allowed
from app.core.on_demand_briefing import run_pending_v7_requests
from app.core.scheduled_batch import ai_extra_headers_from_settings
from app.db.session import get_session_factory


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Process pending on-demand v7 briefings.")
    parser.add_argument("--max-requests", type=int, default=10)
    parser.add_argument("--confirm-local-dev-write", action="store_true")
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    ensure_local_dev_write_allowed(settings.env, args.confirm_local_dev_write)
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
    session = get_session_factory()()
    try:
        results = run_pending_v7_requests(
            session,
            client,
            settings.openai_model,
            max_requests=min(max(args.max_requests, 1), 50),
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
