"""Public URL boundary tests shared by report response schemas."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.schemas.issues import ContextSourceOut, V7SourceOut

NOW = datetime(2026, 7, 12, 5, 0, tzinfo=UTC)


@pytest.mark.parametrize(
    "url,domain",
    [
        ("https://localhost/internal", "localhost"),
        ("https://127.0.0.1/admin", "127.0.0.1"),
        ("https://10.0.0.1/admin", "10.0.0.1"),
        ("https://[::1]/admin", "::1"),
    ],
)
def test_context_source_rejects_local_network_urls(url, domain):
    with pytest.raises(ValidationError, match="Public source URL"):
        ContextSourceOut(
            title="Source",
            url=url,
            domain=domain,
            published_at=NOW,
            source_type="official",
        )


def test_v7_source_rejects_local_network_url():
    with pytest.raises(ValidationError, match="V7 public source URL"):
        V7SourceOut(
            id="source:fixture",
            context_ref="context:fixture",
            citation_id="citation:fixture",
            title="Source",
            url="https://192.168.1.10/internal",
            domain="192.168.1.10",
            source_level="A",
            supported_claims=[
                {
                    "ref": "claim:fixture",
                    "text": "Stored claim",
                    "excerpt": "Stored excerpt",
                    "citation_id": "citation:fixture",
                }
            ],
            retrieved_at=NOW,
        )


def test_public_source_domain_remains_accepted():
    source = ContextSourceOut(
        title="Source",
        url="https://example.gov/document",
        domain="example.gov",
        published_at=NOW,
        source_type="official",
    )

    assert source.url == "https://example.gov/document"
