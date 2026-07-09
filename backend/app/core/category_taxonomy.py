"""Display-oriented category grouping for issue filters.

The stored source category is intentionally preserved on issue rows for
provenance. This module derives Korean filter labels from the stored category
and title so the dashboard can show user-readable groupings such as
`우크라이나 전쟁` without a schema migration.
"""

import re

KOREAN_CATEGORY_ORDER = [
    "우크라이나 전쟁",
    "이란 전쟁",
    "이스라엘·가자",
    "국제 안보",
    "미국 정치",
    "브라질 정치",
    "영국 정치",
    "프랑스 정치",
    "스페인 정치",
    "러시아 정치",
    "중국 정치",
    "튀르키예 정치",
    "가상자산",
    "AI·기술",
    "기업·산업",
    "미국 사법",
    "스포츠",
    "정치",
    "기술",
    "경제",
    "환경",
    "세계",
]

_RAW_CATEGORY_LABELS = {
    "airdrops": "가상자산",
    "bitcoin": "가상자산",
    "crypto": "가상자산",
    "token launch": "가상자산",
    "ipo": "기업·산업",
    "openai": "AI·기술",
    "tech": "AI·기술",
    "hfc": "중국 정치",
    "parent for derivative": "미국 정치",
    "president": "미국 정치",
    "primary elections": "미국 정치",
    "senate": "미국 정치",
    "trump": "미국 정치",
    "trump presidency": "국제 안보",
    "trump-putin": "국제 안보",
    "united states": "미국 정치",
    "us election": "미국 정치",
    "bernie sanders": "미국 정치",
    "supreme court": "미국 사법",
    "supreme court ": "미국 사법",
    "sports": "스포츠",
    "soccer": "스포츠",
    "economy": "경제",
    "environment": "환경",
    "technology": "기술",
    "world": "세계",
    "politics": "정치",
}


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().casefold())


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def _append_unique(labels: list[str], label: str) -> None:
    if label not in labels:
        labels.append(label)


def issue_category_labels(title: str, category: str) -> tuple[str, ...]:
    """Return Korean filter labels for one issue.

    Labels are intentionally many-to-one friendly: one issue can belong to a
    specific topic group such as `우크라이나 전쟁` and a broader group such as
    `국제 안보`.
    """

    normalized_title = _normalize(title)
    normalized_category = _normalize(category)
    text = f"{normalized_title} {normalized_category}"
    labels: list[str] = []

    if _contains_any(text, ("iran", "tehran")):
        _append_unique(labels, "이란 전쟁")

    if _contains_any(
        text,
        (
            "ukraine",
            "zelenskyy",
            "kostyantynivka",
            "lyman",
            "sumy",
            "russian sovereignty",
        ),
    ):
        _append_unique(labels, "우크라이나 전쟁")

    if _contains_any(text, ("gaza", "hamas", "israel", "israeli", "netanyahu")):
        _append_unique(labels, "이스라엘·가자")

    if _contains_any(
        text,
        (
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
        _append_unique(labels, "국제 안보")

    if _contains_any(
        text,
        (
            "trump",
            "jd vance",
            "gavin newsom",
            "republican",
            "democratic",
            "senate",
            "house",
            "midterm",
            "michigan",
            "tx-sen",
            "united states",
            "us presidential",
            "us election",
        ),
    ):
        _append_unique(labels, "미국 정치")

    if _contains_any(text, ("brazil", "tarcisio", "ronaldo caiado")):
        _append_unique(labels, "브라질 정치")

    if _contains_any(text, ("uk election", "next uk election")):
        _append_unique(labels, "영국 정치")

    if _contains_any(text, ("france", "macron")):
        _append_unique(labels, "프랑스 정치")

    if _contains_any(text, ("spain", "spanish")):
        _append_unique(labels, "스페인 정치")

    if _contains_any(text, ("putin", "president of russia")):
        _append_unique(labels, "러시아 정치")

    if _contains_any(text, ("xi jinping", "china")) and "china x india" not in text:
        _append_unique(labels, "중국 정치")

    if _contains_any(text, ("erdoğan", "erdogan", "turkey", "türkiye")):
        _append_unique(labels, "튀르키예 정치")

    if _contains_any(
        text,
        (
            "crypto",
            "bitcoin",
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
        ),
    ):
        _append_unique(labels, "가상자산")

    if _contains_any(text, ("openai", "gpt", "hardware", "tech")):
        _append_unique(labels, "AI·기술")

    if _contains_any(text, ("ipo", "initial public offering")):
        _append_unique(labels, "기업·산업")

    if _contains_any(text, ("scotus", "supreme court")):
        _append_unique(labels, "미국 사법")

    if _contains_any(text, ("fifa", "world cup", "ballon d'or", "soccer")):
        _append_unique(labels, "스포츠")

    if not labels:
        fallback = _RAW_CATEGORY_LABELS.get(normalized_category)
        _append_unique(labels, fallback or category.strip() or "기타")

    return tuple(labels)


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
