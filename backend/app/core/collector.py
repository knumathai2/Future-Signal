import json
import logging
import urllib.error
import urllib.request
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

GAMMA_EVENTS_URL = "https://gamma-api.polymarket.com/events"
NORMALIZED_SAMPLES_PATH = "normalized_samples.json"
SKIPPED_RECORDS_PATH = "skipped_records.json"

EXCLUDED_SAMPLE_TAG_SLUGS = {
    "celebrities",
    "culture",
    "music",
    "pop-culture",
    "taylor-swift",
}
EXCLUDED_SAMPLE_TITLE_TERMS = ("pregnant",)
VOLUME_24H_KEYS = ("volume24hr", "volume24hrClob", "volume24hrAmm")
VOLUME_TOTAL_KEYS = ("volume", "volumeNum", "volumeClob")
LIQUIDITY_KEYS = ("liquidity", "liquidityNum", "liquidityClob")


def parse_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_json_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if not value or not isinstance(value, str):
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


def parse_source_date(value: Any) -> date | None:
    if not value or not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None


def first_float(source: dict[str, Any], keys: tuple[str, ...]) -> float | None:
    for key in keys:
        parsed = parse_float(source.get(key))
        if parsed is not None:
            return parsed
    return None


def skip_record(event_id: Any, reason: str, **details: Any) -> dict[str, Any]:
    record = {"event_id": event_id, "reason": reason}
    record.update({key: value for key, value in details.items() if value not in (None, [], {})})
    return record


def market_skip_reason(market: dict[str, Any], reason: str) -> str:
    return f"Market {market.get('id')}: {reason}"


def tag_slugs(raw_tags: list[Any]) -> set[str]:
    return {
        (tag.get("slug") or "").lower()
        for tag in raw_tags
        if isinstance(tag, dict) and tag.get("slug")
    }


def primary_category(raw_tags: list[Any]) -> str:
    for tag in raw_tags:
        if isinstance(tag, dict) and tag.get("label"):
            return str(tag["label"])
    return "Uncategorized"


def build_display_description(category: str) -> str:
    return (
        "Tracks reflected expectation in public prediction-market data for this "
        f"{category.lower()} issue. Interpret changes with caution and verify source context."
    )


def build_market_candidate(
    market: dict[str, Any],
    event_end_date: Any,
    as_of_date: date,
) -> tuple[dict[str, Any] | None, str | None]:
    outcomes = parse_json_list(market.get("outcomes", "[]"))
    if outcomes != ["Yes", "No"]:
        return None, market_skip_reason(market, f"Non-binary outcomes {outcomes}")

    if market.get("closed") is True or not market.get("active"):
        return None, market_skip_reason(market, "Closed or inactive")

    end_date = market.get("endDate") or event_end_date
    parsed_end_date = parse_source_date(end_date)
    if not end_date:
        return None, market_skip_reason(market, "Missing end date")
    if parsed_end_date is None:
        return None, market_skip_reason(market, f"Invalid end date {end_date}")
    if parsed_end_date < as_of_date:
        return None, market_skip_reason(market, f"End date {end_date} is in the past")

    prices = parse_json_list(market.get("outcomePrices", "[]"))
    current_value = parse_float(prices[0]) if prices else None
    if current_value is None or current_value <= 0:
        return None, market_skip_reason(market, "Invalid or zero current value")

    volume_24h = first_float(market, VOLUME_24H_KEYS)
    volume_total = first_float(market, VOLUME_TOTAL_KEYS)
    liquidity = first_float(market, LIQUIDITY_KEYS)
    required_values = {
        "question": market.get("question"),
        "volume_24h": volume_24h,
        "volume_total": volume_total,
        "liquidity": liquidity,
        "conditionId": market.get("conditionId"),
        "createdAt": market.get("createdAt"),
    }
    missing = [name for name, value in required_values.items() if value in (None, "")]
    if missing:
        return None, market_skip_reason(market, f"Missing required fields {missing}")

    clob_token_ids = parse_json_list(market.get("clobTokenIds", "[]"))
    return {
        "current_value": current_value,
        "volume_24h": volume_24h,
        "volume_total": volume_total,
        "liquidity": liquidity,
        "end_date": end_date,
        "clob_token_ids": clob_token_ids,
    }, None


def normalize_event(
    item: dict[str, Any],
    as_of_date: date | None = None,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    as_of = as_of_date or datetime.now(UTC).date()
    raw_tags = item.get("tags") or []
    slugs = tag_slugs(raw_tags)
    source_text = " ".join(
        value or "" for value in (item.get("title"), item.get("description"))
    ).lower()

    if slugs & EXCLUDED_SAMPLE_TAG_SLUGS or any(
        term in source_text for term in EXCLUDED_SAMPLE_TITLE_TERMS
    ):
        return None, skip_record(
            item.get("id"),
            "Excluded tag or title term",
            tags=sorted(slugs),
            title=item.get("title"),
        )

    market_skip_reasons = []
    valid_market = None
    candidate = None
    for market in item.get("markets", []):
        candidate, reason = build_market_candidate(market, item.get("endDate"), as_of)
        if reason:
            market_skip_reasons.append(reason)
            continue
        valid_market = market
        break

    if valid_market is None or candidate is None:
        return None, skip_record(
            item.get("id"),
            "No valid binary market found",
            market_skip_reasons=market_skip_reasons,
        )

    category = primary_category(raw_tags)
    clob_token_ids = candidate["clob_token_ids"]
    history_token = clob_token_ids[0] if clob_token_ids else None

    sample = {
        "id": item.get("id"),
        "market_id": valid_market.get("id"),
        "polymarket_condition_id": valid_market.get("conditionId"),
        "title": valid_market.get("question"),
        "description": build_display_description(category),
        "category": category,
        "status": "active",
        "outcome_type": "binary",
        "outcome_label": "Yes",
        "current_value": candidate["current_value"],
        "volume_24h": candidate["volume_24h"],
        "volume_total": candidate["volume_total"],
        "liquidity": candidate["liquidity"],
        "market_created_at": valid_market.get("createdAt"),
        "end_date": candidate["end_date"],
        "event_created_at": item.get("createdAt"),
        "event_updated_at": item.get("updatedAt"),
        "event_end_date": item.get("endDate"),
        "clob_token_ids": clob_token_ids,
        "price_history_token": history_token,
        "price_history_source": "CLOB" if history_token else None,
        "source_metadata": {
            "event_title": item.get("title"),
            "tag_slugs": sorted(slugs),
            "resolution_source_present": bool(
                item.get("resolutionSource") or valid_market.get("resolutionSource")
            ),
            "description_policy": "raw_source_descriptions_omitted",
        },
    }
    return sample, None


def fetch_json(url: str) -> list[dict[str, Any]]:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as response:
        data = json.loads(response.read().decode("utf-8"))
    return data if isinstance(data, list) else []


def write_json(path: Path, payload: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2)
        file.write("\n")


def fetch_events(
    limit: int = 100,
    max_samples: int = 50,
    output_dir: str | Path = ".",
) -> list[dict[str, Any]]:
    samples = []
    skipped_records = []
    offset = 0

    while len(samples) < max_samples:
        current_url = (
            f"{GAMMA_EVENTS_URL}?limit={limit}&active=true&closed=false&offset={offset}"
        )
        logger.info("Fetching events from Gamma API (offset=%s)...", offset)
        try:
            data = fetch_json(current_url)
        except (TimeoutError, urllib.error.URLError, json.JSONDecodeError) as exc:
            logger.error("Failed to fetch events: %s", exc)
            break

        if not data:
            logger.info("No more events returned from API.")
            break

        for item in data:
            if len(samples) >= max_samples:
                break

            try:
                sample, skipped = normalize_event(item)
            except Exception as exc:
                logger.warning("Failed to process event %s: %s. Skipping.", item.get("id"), exc)
                skipped_records.append(
                    skip_record(item.get("id"), "Exception during processing", error=str(exc))
                )
                continue

            if skipped:
                skipped_records.append(skipped)
                continue

            if sample:
                samples.append(sample)

        offset += limit

    output_path = Path(output_dir)
    write_json(output_path / NORMALIZED_SAMPLES_PATH, samples)
    write_json(output_path / SKIPPED_RECORDS_PATH, skipped_records)

    logger.info("Successfully extracted %s samples.", len(samples))
    logger.info("Skipped %s records. Details in %s.", len(skipped_records), SKIPPED_RECORDS_PATH)
    return samples


if __name__ == "__main__":
    fetch_events(max_samples=50)
