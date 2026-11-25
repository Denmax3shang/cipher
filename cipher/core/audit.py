import json
from datetime import datetime

from cipher.core import memory

SAFE = {"host", "ports", "port", "domain", "url", "query", "filename",
        "city", "topic", "algo", "when", "post_id", "length", "method", "action"}
ICON = {"ok": "✅", "blocked": "🚫", "error": "⚠️", "pending": "⏳"}
MAX_BYTES = 1_000_000


def _path():
    return memory.DATA_DIR / "audit.log"


def record(mode, tool, args, result):
    try:
        res = str(result)
        status = ("blocked" if res.startswith("BLOCKED")
                  else "pending" if res.startswith("Approval requested")
                  else "error" if res.startswith("Error") else "ok")
        entry = {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "mode": mode,
            "tool": tool,
            "args": {k: (str(v)[:100] if k in SAFE else "<redacted>")
                     for k, v in args.items()},
            "status": status,
        }
        p = _path()
        if p.exists() and p.stat().st_size > MAX_BYTES:
            p.write_text("\n".join(p.read_text().splitlines()[-500:]) + "\n")
        with p.open("a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass


def _entries():
    p = _path()
    if not p.exists():
        return []
    out = []
    for line in p.read_text().splitlines():
        try:
            out.append(json.loads(line))
        except ValueError:
            continue
    return out


def count():
    return len(_entries())


def tail(n=10):
    rows = _entries()[-n:]
    if not rows:
        return "No tool activity logged yet."
    lines = []
    for e in rows:
        args = " ".join(f"{k}={v}" for k, v in e["args"].items())
        lines.append(f"{ICON.get(e['status'], '?')} {e['time'][5:16]} "
                     f"[{e['mode']}] {e['tool']} {args}".strip())
    return "\n".join(lines)


def recent(hours=24):
    from datetime import timedelta
    cutoff = (datetime.now() - timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
    return [e for e in _entries() if e["time"] >= cutoff]


def recent(hours=24):
    from datetime import timedelta
    cutoff = (datetime.now() - timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
    return [e for e in _entries() if e["time"] >= cutoff]
