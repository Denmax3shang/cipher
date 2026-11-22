from datetime import datetime

from cipher.config import API_KEY, BASE_URL, MODEL
from cipher.core import audit, brain, limiter, memory, scheduler
from cipher.personality import MODES


def status():
    host = BASE_URL.split("//")[-1].split("/")[0]
    mode = brain.get_mode()
    return "\n".join([
        "🛰️ CIPHER status",
        f"Mode: {MODES[mode]['emoji']} {mode}",
        f"Model: {MODEL} via {host}",
        f"LLM key: {'set ✅' if API_KEY else 'missing ❌'}",
        f"Voice replies: {'on' if memory.voice_on() else 'off'}",
        f"Scope hosts: {len(memory.get_scope())}",
        f"Facts: {len(memory.get_facts())} | Notes: {len(memory.load_json('notes.json', []))}",
        f"Scheduled posts: {len(scheduler.list_posts())}",
        f"Tool calls logged: {audit.count()}",
        limiter.summary(),
    ])


def make_export():
    out_dir = memory.DATA_DIR / "exports"
    out_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now()
    path = out_dir / f"cipher-export-{now:%Y%m%d-%H%M}.md"
    lines = ["# CIPHER export", f"Exported {now:%Y-%m-%d %H:%M}", "", "## Facts about you"]
    lines += [f"- {f}" for f in memory.get_facts()] or ["(none)"]
    lines += ["", "## Notes"]
    lines += [f"{i}. {n}" for i, n in enumerate(memory.load_json("notes.json", []), 1)] \
        or ["(none)"]
    lines += ["", "## Scheduled posts"]
    lines += [f"- #{p['id']} {p['when']}: {p['text']}" for p in scheduler.list_posts()] \
        or ["(none)"]
    lines += ["", "## Current conversation"]
    chat = [m for m in brain.history if m["role"] in ("user", "assistant") and m.get("content")]
    for m in chat:
        lines.append(f"**{'You' if m['role'] == 'user' else 'CIPHER'}:** {m['content']}")
    if not chat:
        lines.append("(empty)")
    path.write_text("\n".join(lines) + "\n")
    return path
