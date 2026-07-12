"""Deterministic safety checks for source URLs exposed by the public API."""

from ipaddress import ip_address
from urllib.parse import SplitResult, urlsplit


def parse_public_http_url(url: str) -> SplitResult | None:
    """Parse an absolute public HTTP(S) URL, rejecting local network targets."""
    try:
        parsed = urlsplit(url.strip())
        _ = parsed.port
    except ValueError:
        return None

    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        return None
    if parsed.username or parsed.password:
        return None

    host = parsed.hostname.casefold().rstrip(".")
    if not host or host == "localhost" or host.endswith(".localhost"):
        return None

    try:
        address = ip_address(host)
    except ValueError:
        # Single-label and numeric-looking hosts may resolve to a local target in
        # browsers even though they are not canonical IP address strings.
        if "." not in host and ":" not in host:
            return None
        if all(character.isdigit() or character == "." for character in host):
            return None
    else:
        if not address.is_global or address.is_multicast:
            return None

    return parsed
