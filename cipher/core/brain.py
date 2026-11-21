import json
from datetime import datetime
import requests
from cipher.config import API_KEY, BASE_URL, MODEL, MAX_HISTORY
from cipher.personality import BASE, MODES, DEFAULT_MODE
from cipher.core.memory import get_facts, load_json, save_json
from cipher.core import audit
from cipher.skills import TOOLS, load_all

load_all()
history = []
_mode = load_json("state.json", {}).get("mode", DEFAULT_MODE)
if _mode not in MODES:
    _mode = DEFAULT_MODE


def get_mode():
    return _mode


def set_mode(name):
    global _mode
    if name not in MODES:
        return False
    _mode = name
    history.clear()
    save_json("state.json", {"mode": name})
    return True


def reset():
    history.clear()


def _allowed():
    allowed = MODES[_mode]["tools"]
    return [n for n in TOOLS if allowed is None or n in allowed]


def _tools():
    return [{"type": "function",
             "function": {"name": TOOLS[n]["schema"]["name"],
                          "description": TOOLS[n]["schema"]["description"],
                          "parameters": TOOLS[n]["schema"]["input_schema"]}}
            for n in _allowed()]


def _call():
    facts = "\n".join(f"- {f}" for f in get_facts()) or "- none yet"
    system = {"role": "system",
              "content": BASE.format(now=datetime.now().strftime("%A %Y-%m-%d %H:%M"), mode=_mode, mode_prompt=MODES[_mode]["prompt"], facts=facts)}
    body = {"model": MODEL, "messages": [system] + history, "max_tokens": 1500}
    tools = _tools()
    if tools:
        body["tools"] = tools
    r = requests.post(f"{BASE_URL}/chat/completions",
                      headers={"Authorization": f"Bearer {API_KEY}"},
                      json=body, timeout=25)
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
            name = c["function"]["name"]
            args = {}
            try:
                if name not in _allowed():
                    raise RuntimeError("tool not available in this mode")
                args = json.loads(c["function"]["arguments"] or "{}")
                out = TOOLS[name]["func"](**args)
            except Exception as e:
                out = f"Error: {e}"
            audit.record(_mode, name, args, out)
            history.append({"role": "tool", "tool_call_id": c["id"], "content": str(out)})
    return "Too many steps. Try rephrasing."
