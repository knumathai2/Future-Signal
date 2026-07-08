import json
from datetime import datetime, timezone

def process_samples():
    with open("gamma_response_sample.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    samples = []
    missing_unstable = set()

    for item in data:
        if len(samples) >= 10:
            break

        # active binary market check:
        # Polymarket events usually contain "markets", and binary ones have outcomes ["Yes", "No"]

        valid_market = None
        for market in item.get("markets", []):
            outcomes = json.loads(market.get("outcomes", "[]"))
            if outcomes != ["Yes", "No"]:
                continue

            if market.get("closed") is True or not market.get("active"):
                continue

            end_date_str = market.get("endDate", "")
            if end_date_str < "2026-07-08":
                continue

            prices = json.loads(market.get("outcomePrices", "[]"))
            current_value = float(prices[0]) if prices else 0.0
            if current_value <= 0:
                continue

            valid_market = market
            break

        if not valid_market:
            continue

        market = valid_market
        clob_token_ids = json.loads(market.get("clobTokenIds", "[]"))
        history_token = clob_token_ids[0] if clob_token_ids else None

        raw_tags = item.get("tags") or []

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
                "neutral_title": "Outlook on this issue",  # Placeholder for AI-generated neutral title
                "neutral_tags": [{"label": "Issue change", "slug": "issue-change"}, {"label": "Public data", "slug": "public-data"}],
            },
            "metrics": {
                "current_value": current_value,
                "volume": item.get("volume"),
                "liquidity": item.get("liquidity"),
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

        # Check for missing/unstable fields
        if not sample["raw_data"]["category_tag"]:
            missing_unstable.add("tags (often empty or missing)")
        if not sample["raw_data"]["resolution_source"]:
            missing_unstable.add("resolutionSource (often empty or missing in both event and market)")

        samples.append(sample)

    with open("polymarket_samples.json", "w", encoding="utf-8") as f:
        json.dump(samples, f, indent=2)

    print("Samples extracted:", len(samples))
    print("Missing/Unstable fields identified:", list(missing_unstable))

if __name__ == "__main__":
    process_samples()
