import time
import uuid
from threading import Lock

TTL = 600  # seconds an approval request stays valid

_lock = Lock()
_pending = {}
_new = []


def _purge():
    now = time.time()
    for k in [k for k, v in _pending.items() if now - v["created"] > TTL]:
        _pending.pop(k, None)


def create(mode, tool, args, chat):
    with _lock:
        _purge()
        aid = uuid.uuid4().hex[:8]
        _pending[aid] = {"mode": mode, "tool": tool, "args": args,
                         "chat": chat, "created": time.time()}
        _new.append(aid)
        return aid


def drain():
    """Return and clear the list of approval IDs created since the last drain."""
    with _lock:
        ids, _new[:] = list(_new), []
        return ids


def get(aid):
    """Peek at a pending approval without removing it."""
    with _lock:
        return _pending.get(aid)


def take(aid):
    """Remove and return a pending approval (use when resolving it)."""
    with _lock:
        return _pending.pop(aid, None)
