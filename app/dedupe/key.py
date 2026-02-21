from typing import Tuple

from app.normalize import normalize_text


def dedup_key(description: str, contact: str) -> Tuple[str, str]:
    d_norm = normalize_text(description)[:200]
    c_norm = normalize_text(contact)
    return d_norm, c_norm


