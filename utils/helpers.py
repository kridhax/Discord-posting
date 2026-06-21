import time
import hashlib
import config
from collections import OrderedDict

_last_post_time: float = 0.0
_seen_hashes: OrderedDict = OrderedDict()
_MAX_SEEN = 200


def is_rate_limited() -> bool:
    """Return True if we're still within the rate limit window."""
    elapsed = time.time() - _last_post_time
    return elapsed < config.RATE_LIMIT_SECONDS


def mark_last_post_time():
    global _last_post_time
    _last_post_time = time.time()


def is_duplicate(content: str) -> bool:
    """Return True if we've seen this exact message recently."""
    h = _hash(content)
    if h in _seen_hashes:
        return True
    _seen_hashes[h] = None
    if len(_seen_hashes) > _MAX_SEEN:
        _seen_hashes.popitem(last=False)
    return False


def _hash(text: str) -> str:
    return hashlib.md5(text.strip().lower().encode()).hexdigest()


def truncate(text: str, max_len: int = 63206) -> str:
    """Facebook posts have a ~63,206 char limit."""
    if len(text) <= max_len:
        return text
    return text[:max_len - 3] + "..."
