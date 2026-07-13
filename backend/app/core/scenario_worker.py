"""Guarded local/development CLI for one queued scenario request."""

import argparse
from uuid import UUID

from app.core.ai_report import build_openai_client
from app.core.config import settings
from app.core.generation_runtime import ensure_generation_worker_allowed
from app.core.scenario_writer import process_scenario_request
from app.core.scheduled_batch import ai_extra_headers_from_settings
from app.db.session import get_session_factory


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Process one queued scenario request.")
    parser.add_argument("--request-id", type=UUID, required=True)
    parser.add_argument("--confirm-generation-write", action="store_true")
    return parser


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
    db = get_session_factory()()
    try:
        result = process_scenario_request(
            db,
            args.request_id,
            client,
            settings.openai_model,
        )
    finally:
        db.close()
    print(f"state={result.state} error_code={result.error_code or '-'}")
    return 0 if result.state == "succeeded" else 1


if __name__ == "__main__":
    raise SystemExit(main())
