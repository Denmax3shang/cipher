import os
import time
from collections import deque
from datetime import date

from cipher.core import memory


def _env_int(name, default):
    try:
        return max(1, int(os.environ.get(name, default)))
    except ValueError:
        return default


PER_MIN = _env_int("RATE_PER_MIN", 20)
PER_DAY = _env_int("RATE_PER_DAY", 400)

_recent = deque()


class RateLimited(Exception):
    pass


def _usage():
    u = memory.load_json("usage.json", {})
    today = date.today().isoformat()
    if u.get("day") != today:
        u = {"day": today, "calls": 0}
    return u


def check(now=None):
    """Count one model call, or raise RateLimited if a limit is hit."""
    now = time.time() if now is None else now
    while _recent and now - _recent[0] > 60:
        _recent.popleft()
    if len(_recent) >= PER_MIN:
        wait = int(60 - (now - _recent[0])) + 1
        raise RateLimited(f"Slow down: limit is {PER_MIN} model calls per minute. "
                          f"Try again in {wait}s.")
    u = _usage()
    if u["calls"] >= PER_DAY:
        raise RateLimited(f"Daily limit reached ({PER_DAY} model calls). It resets at "
                          "midnight, or raise RATE_PER_DAY.")
    _recent.append(now)
    u["calls"] += 1
    memory.save_json("usage.json", u)


def summary():
    u = _usage()
    now = time.time()
    last_min = sum(1 for t in _recent if now - t <= 60)
    return f"API calls today: {u['calls']}/{PER_DAY} | last minute: {last_min}/{PER_MIN}"
