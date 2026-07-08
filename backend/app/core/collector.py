import json
import logging
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

EXCLUDED_SAMPLE_TAG_SLUGS = {
    "celebrities",
    "culture",
    "music",
    "pop-culture",
    "taylor-swift",
}
EXCLUDED_SAMPLE_TITLE_TERMS = ("pregnant",)

def parse_float(value):
    if value in (None, ""):
        return None
    try:
        return float(value)
    except ValueError:
        return None

def fetch_events(limit: int = 100, max_samples: int = 50):
    url = "https://gamma-api.polymarket.com/events"
    samples = []
    offset = 0
    missing_unstable = set()

    while len(samples) < max_samples:
        params = {
            "limit": limit,
            "offset": offset,
            "active": "true",
            "closed": "false"
        }
        logger.info(f"Fetching events from Gamma API (offset={offset})...")
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            logger.error(f"Failed to fetch events: {e}")
            break

        if not data:
            logger.info("No more events returned from API.")
            break

        for item in data:
            if len(samples) >= max_samples:
                break
                
            try:
                # Filter logic
                raw_tags = item.get("tags") or []
                tag_slugs = {
                    (tag.get("slug") or "").lower()
                    for tag in raw_tags
                    if isinstance(tag, dict)
                }
                title_text = " ".join(
                    value or ""
                    for value in (item.get("title"), item.get("description"))
                ).lower()
                
                if tag_slugs & EXCLUDED_SAMPLE_TAG_SLUGS or any(
                    term in title_text for term in EXCLUDED_SAMPLE_TITLE_TERMS
                ):
                    continue

                valid_market = None
                for market in item.get("markets", []):
                    outcomes_str = market.get("outcomes", "[]")
                    if outcomes_str == "[]":
                        continue
                    try:
                        outcomes = json.loads(outcomes_str)
                    except json.JSONDecodeError:
                        continue
                        
                    if outcomes != ["Yes", "No"]:
                        continue

                    if market.get("closed") is True or not market.get("active"):
                        continue

                    end_date_str = market.get("endDate", "")
                    if end_date_str and end_date_str < "2026-07-08":
                        continue

                    prices_str = market.get("outcomePrices", "[]")
                    try:
                        prices = json.loads(prices_str)
                    except json.JSONDecodeError:
                        continue
                        
                    current_value = parse_float(prices[0]) if prices else None
                    if current_value is None or current_value <= 0:
                        continue

                    valid_market = market
                    break

                if not valid_market:
                    continue

                market = valid_market
                
                clob_token_ids_str = market.get("clobTokenIds", "[]")
                try:
                    clob_token_ids = json.loads(clob_token_ids_str)
                except json.JSONDecodeError:
                    clob_token_ids = []
                    
                history_token = clob_token_ids[0] if clob_token_ids else None

                sample = {
                    "id": item.get("id"),
                    "market_id": market.get("id"),
                    "raw_data": {
                        "title": market.get("question"),
                        "description": market.get("description"),
                        "event_title": item.get("title"),
                        "event_description": item.get("description"),
                        "category_tag": raw_tags,
                        "resolution_source": item.get("resolutionSource") or market.get("resolutionSource"),
                    },
                    "ui_display": {
                        "neutral_title": "Outlook on this issue",
                        "neutral_tags": [
                            {"label": "Issue change", "slug": "issue-change"},
                            {"label": "Public data", "slug": "public-data"},
                        ],
                    },
                    "metrics": {
                        "current_value": current_value,
                        "volume": parse_float(
                            market.get("volume") or market.get("volumeNum") or market.get("volumeClob")
                        ),
                        "liquidity": parse_float(
                            market.get("liquidity")
                            or market.get("liquidityNum")
                            or market.get("liquidityClob")
                        ),
                    },
                    "clobTokenIds": clob_token_ids,
                    "price_history_token": history_token,
                    "price_history_source": "CLOB" if history_token else None,
                    "created_at": market.get("createdAt"),
                    "updated_at": market.get("updatedAt"),
                    "end_date": market.get("endDate"),
                    "event_created_at": item.get("createdAt"),
                    "event_updated_at": item.get("updatedAt"),
                    "event_end_date": item.get("endDate")
                }

                if not sample["raw_data"]["category_tag"]:
                    missing_unstable.add("tags (often empty or missing)")
                if not sample["raw_data"]["resolution_source"]:
                    missing_unstable.add(
                        "resolutionSource (often empty or missing in both event and market)"
                    )

                samples.append(sample)
            except Exception as e:
                logger.warning(f"Failed to process event {item.get('id')}: {e}. Skipping.")

        offset += limit
        
    with open("normalized_samples.json", "w", encoding="utf-8") as f:
        json.dump(samples, f, indent=2)

    logger.info(f"Successfully extracted {len(samples)} samples.")
    logger.info(f"Missing/Unstable fields identified: {list(missing_unstable)}")

if __name__ == "__main__":
    fetch_events(max_samples=50)
