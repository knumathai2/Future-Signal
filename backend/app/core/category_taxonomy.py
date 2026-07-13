"""Broad Korean category grouping for dashboard filters.

Stored source categories stay unchanged on issue rows. This module derives a
small set of broad Korean filter labels so the dashboard filter remains simple
(`정치`, `경제`, `기술`, `세계`, ...), while issue cards can keep their richer
topic labels in the frontend display layer.
"""

import re

KOREAN_CATEGORY_ORDER = [
    "정치",
    "경제",
    "환경",
    "기술",
    "세계",
    "스포츠",
    "기타",
]

_RAW_CATEGORY_LABELS = {
    "airdrops": "경제",
    "bernie sanders": "정치",
    "bitcoin": "경제",
    "crypto": "경제",
    "economy": "경제",
    "environment": "환경",
    "hfc": "정치",
    "ipo": "경제",
    "openai": "기술",
    "parent for derivative": "정치",
    "politics": "정치",
    "president": "정치",
    "primary elections": "정치",
    "senate": "정치",
    "soccer": "스포츠",
    "sports": "스포츠",
    "supreme court": "정치",
    "tech": "기술",
    "technology": "기술",
    "token launch": "경제",
    "trump": "정치",
    "trump presidency": "세계",
    "trump-putin": "세계",
    "uk": "정치",
    "united states": "정치",
    "us election": "정치",
    "world": "세계",
}


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().casefold())


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def issue_category_labels(title: str, category: str) -> tuple[str, ...]:
    """Return broad Korean filter labels for one issue."""

    normalized_title = _normalize(title)
    normalized_category = _normalize(category)
    text = f"{normalized_title} {normalized_category}"

    if _contains_any(
        text,
        (
            "crypto",
            "bitcoin",
            "stablecoin",
            "tether",
            "usdc",
            "usdt",
            "token",
            "airdrop",
            "kraken",
            "metamask",
            "pump.fun",
            "megaeth",
            "base",
            "ostium",
            "abstract",
            "axiom",
            "unit",
            "hyperliquid",
            "ipo",
        ),
    ):
        return ("경제",)

    if _contains_any(text, ("openai", "gpt", "hardware", "tech")):
        return ("기술",)

    if _contains_any(text, ("fifa", "world cup", "ballon d'or", "soccer")):
        return ("스포츠",)

    if _contains_any(
        text,
        (
            "ukraine",
            "zelenskyy",
            "kostyantynivka",
            "lyman",
            "sumy",
            "iran",
            "tehran",
            "gaza",
            "hamas",
            "israel",
            "israeli",
            "netanyahu",
            "military clash",
            "nato",
            "nuclear deal",
            "taiwan",
            "annex",
            "sovereignty",
            "china x india",
            "u.s. x russia",
            "us x russia",
        ),
    ):
        return ("세계",)

    if _contains_any(
        text,
        (
            "politics",
            "election",
            "president",
            "parliament",
            "senate",
            "house",
            "midterm",
            "trump",
            "jd vance",
            "gavin newsom",
            "republican",
            "democratic",
            "brazil",
            "tarcisio",
            "ronaldo caiado",
            "france",
            "macron",
            "spain",
            "spanish",
            "putin",
            "xi jinping",
            "erdoğan",
            "erdogan",
            "uk election",
            "supreme court",
            "scotus",
        ),
    ):
        return ("정치",)

    fallback = _RAW_CATEGORY_LABELS.get(normalized_category)
    return (fallback or "기타",)


def category_matches(title: str, source_category: str, requested_category: str) -> bool:
    requested = _normalize(requested_category)
    if _normalize(source_category) == requested:
        return True
    return any(
        _normalize(label) == requested
        for label in issue_category_labels(title, source_category)
    )


def sort_category_labels(labels: set[str]) -> list[str]:
    order = {label: index for index, label in enumerate(KOREAN_CATEGORY_ORDER)}
    return sorted(labels, key=lambda label: (order.get(label, len(order)), label))
