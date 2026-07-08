import json
from datetime import date

from app.core.collector import normalize_event


def _event(
    *,
    event_overrides: dict | None = None,
    market_overrides: dict | None = None,
) -> dict:
    event = {
        "id": "event-1",
        "title": "Example policy issue",
        "description": "Raw source description that must not enter the sample artifact.",
        "endDate": "2026-12-31T00:00:00Z",
        "createdAt": "2026-07-01T00:00:00Z",
        "updatedAt": "2026-07-08T00:00:00Z",
        "tags": [{"label": "Politics", "slug": "politics"}],
        "markets": [
            {
                "id": "market-1",
                "question": "Example policy issue by December 2026?",
                "description": "Raw market description that must remain out of display data.",
                "outcomes": json.dumps(["Yes", "No"]),
                "outcomePrices": json.dumps(["0.42", "0.58"]),
                "active": True,
                "closed": False,
                "endDate": "2026-12-31T00:00:00Z",
                "volume24hr": "123.45",
                "volume": "999.5",
                "liquidity": "321.0",
                "conditionId": "0xcondition",
                "createdAt": "2026-06-01T00:00:00Z",
                "clobTokenIds": json.dumps(["yes-token", "no-token"]),
            }
        ],
    }
    if event_overrides:
        event.update(event_overrides)
    if market_overrides:
        event["markets"][0].update(market_overrides)
    return event


def test_normalized_sample_has_safe_display_description_and_required_fields():
    sample, skipped = normalize_event(_event(), as_of_date=date(2026, 7, 8))

    assert skipped is None
    assert sample is not None
    assert isinstance(sample["description"], str)
    assert sample["description"].startswith("Tracks reflected expectation")
    assert sample["source_metadata"]["description_policy"] == "raw_source_descriptions_omitted"

    required_fields = [
        "title",
        "description",
        "category",
        "status",
        "outcome_type",
        "current_value",
        "volume_24h",
        "volume_total",
        "liquidity",
        "polymarket_condition_id",
        "market_created_at",
        "end_date",
    ]
    assert all(sample[field] not in (None, "") for field in required_fields)

    serialized = json.dumps(sample)
    assert "Raw source description" not in serialized
    assert "Raw market description" not in serialized


def test_missing_volume_24h_is_structured_skip():
    event = _event(market_overrides={"volume24hr": None})

    sample, skipped = normalize_event(event, as_of_date=date(2026, 7, 8))

    assert sample is None
    assert skipped is not None
    assert skipped["reason"] == "No valid binary market found"
    assert any("volume_24h" in reason for reason in skipped["market_skip_reasons"])


def test_missing_end_date_is_structured_skip():
    event = _event(
        event_overrides={"endDate": None},
        market_overrides={"endDate": None},
    )

    sample, skipped = normalize_event(event, as_of_date=date(2026, 7, 8))

    assert sample is None
    assert skipped is not None
    assert skipped["reason"] == "No valid binary market found"
    assert any("Missing end date" in reason for reason in skipped["market_skip_reasons"])
