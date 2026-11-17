import json
import requests
from cipher.config import API_KEY, BASE_URL, MODEL, MAX_HISTORY
from cipher.personality import SYSTEM_PROMPT
from cipher.core.memory import get_facts
from cipher.skills import TOOLS, load_all

load_all()
history = []


def reset():
    history.clear()


def _tools():
    return [{"type": "function",
             "function": {"name": t["schema"]["name"],
                          "description": t["schema"]["description"],
                          "parameters": t["schema"]["input_schema"]}}
            for t in TOOLS.values()]


def _call():
    facts = "\n".join(f"- {f}" for f in get_facts()) or "- none yet"
    system = {"role": "system", "content": SYSTEM_PROMPT.format(facts=facts)}
    r = requests.post(
        f"{BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={"model": MODEL, "messages": [system] + history,
              "tools": _tools(), "max_tokens": 1500},
        timeout=25,
    )
    if not r.ok:
        raise RuntimeError(f"{r.status_code}: {r.text[:300]}")
    return r.json()["choices"][0]["message"]


def process_command(text):
    if not API_KEY:
        return "Run: export LLM_API_KEY=your-key"
    history.append({"role": "user", "content": text})
    del history[:-MAX_HISTORY]
    while history and history[0]["role"] != "user":
        history.pop(0)

    for _ in range(6):
        msg = _call()
        entry = {"role": "assistant", "content": msg.get("content") or ""}
        if msg.get("tool_calls"):
            entry["tool_calls"] = msg["tool_calls"]
        history.append(entry)

        if not msg.get("tool_calls"):
            return entry["content"]

        for c in msg["tool_calls"]:
            try:
                args = json.loads(c["function"]["arguments"] or "{}")
                out = TOOLS[c["function"]["name"]]["func"](**args)
            except Exception as e:
                out = f"Error: {e}"
            history.append({"role": "tool", "tool_call_id": c["id"],
                            "content": str(out)})
    return "Too many steps. Try rephrasing."
