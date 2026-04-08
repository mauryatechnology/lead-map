import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def clean_phone(raw: str) -> str:
    if not raw:
        return ""
    # Keep digits, +, -, (, ), spaces
    cleaned = re.sub(r"[^\d\+\-\(\)\s]", "", raw).strip()
    return cleaned


def clean_url(url: str) -> str:
    if not url:
        return ""
    if url.startswith("https://www.google.com/url"):
        from urllib.parse import urlparse, parse_qs, unquote
        try:
            qs = parse_qs(urlparse(url).query)
            return unquote(qs.get("url", [""])[0] or qs.get("q", [""])[0])
        except Exception:
            return url
    return url


def extract_instagram_handle(url: str) -> str:
    if not url:
        return ""
    m = re.search(r"instagram\.com/([^/?#\s]+)", url)
    if m:
        handle = m.group(1).strip("/")
        if handle and handle not in ("p", "explore", "reels", "stories"):
            return f"@{handle}"
    return ""


def extract_city_from_address(address: str, fallback: Optional[str] = None) -> str:
    if not address:
        return fallback or ""
    parts = [p.strip() for p in address.split(",") if p.strip()]
    # Try to return the 3rd-to-last or 2nd-to-last segment (before state/zip/country)
    if len(parts) >= 4:
        return parts[-3]
    elif len(parts) >= 3:
        return parts[-2]
    elif len(parts) >= 2:
        return parts[-2]
    return fallback or ""


def safe_truncate(text: str, max_len: int = 300) -> str:
    if not text:
        return ""
    return text[:max_len].strip()


def validate_maps_url(url: str) -> bool:
    return bool(url and ("google.com/maps" in url or "maps.google" in url))
