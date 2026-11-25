import json
from datetime import datetime

import requests
from cipher.config import API_KEY, BASE_URL, MODEL, MAX_HISTORY
from cipher.personality import BASE, MODES, DEFAULT_MODE
from cipher.core.memory import get_facts, load_json, save_json
from cipher.core import approvals, audit, limiter
from cipher.skills import TOOLS, load_all

load_all()
history = []
_mode = load_json("state.json", {}).get("mode", DEFAULT_MODE)
if _mode not in MODES:
    _mode = DEFAULT_MODE

RISKY = {"port_scan", "crack_hash"}


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


def _system():
    facts = "\n".join(f"- {f}" for f in get_facts()) or "- none yet"
    return {"role": "system",
            "content": BASE.format(now=datetime.now().strftime("%A %Y-%m-%d %H:%M"),
                                   mode=_mode, mode_prompt=MODES[_mode]["prompt"], facts=facts)}


def _call():
    body = {"model": MODEL, "messages": [_system()] + history, "max_tokens": 1500}
    tools = _tools()
    if tools:
        body["tools"] = tools
    r = requests.post(f"{BASE_URL}/chat/completions",
                      headers={"Authorization": f"Bearer {API_KEY}"},
                      json=body, timeout=25)
    if r.status_code == 429:
        raise RuntimeError("The AI provider is rate limiting you. Wait about "
                           f"{r.headers.get('retry-after', '30')} seconds and try again.")
    if not r.ok:
        raise RuntimeError(f"{r.status_code}: {r.text[:300]}")
    return r.json()["choices"][0]["message"]


def _call_stream(emit):
    body = {"model": MODEL, "messages": [_system()] + history,
            "max_tokens": 1500, "stream": True}
    tools = _tools()
    if tools:
        body["tools"] = tools
    r = requests.post(f"{BASE_URL}/chat/completions",
                      headers={"Authorization": f"Bearer {API_KEY}"},
                      json=body, timeout=60, stream=True)
    if r.status_code == 429:
        raise RuntimeError("The AI provider is rate limiting you. Wait about "
                           f"{r.headers.get('retry-after', '30')} seconds and try again.")
    if not r.ok:
        raise RuntimeError(f"{r.status_code}: {r.text[:300]}")

    content, calls = "", {}
    for line in r.iter_lines(decode_unicode=True):
        if not line or not line.startswith("data: "):
            continue
        raw = line[6:]
        if raw.strip() == "[DONE]":
            break
        delta = json.loads(raw)["choices"][0]["delta"]
        if delta.get("content"):
            content += delta["content"]
            emit(delta["content"])
        for tc in delta.get("tool_calls") or []:
            slot = calls.setdefault(tc["index"], {"id": "", "type": "function",
                                                   "function": {"name": "", "arguments": ""}})
            if tc.get("id"):
                slot["id"] = tc["id"]
            fn = tc.get("function", {})
            if fn.get("name"):
                slot["function"]["name"] += fn["name"]
            if fn.get("arguments"):
                slot["function"]["arguments"] += fn["arguments"]
    msg = {"role": "assistant", "content": content}
    if calls:
        msg["tool_calls"] = [calls[i] for i in sorted(calls)]
    return msg


def _run_tools(msg, chat=None):
    for c in msg["tool_calls"]:
        name = c["function"]["name"]
        args = {}
        try:
            if name not in _allowed():
                raise RuntimeError("tool not available in this mode")
            args = json.loads(c["function"]["arguments"] or "{}")
            if chat is not None and name in RISKY:
                aid = approvals.create(_mode, name, args, chat)
                out = (f"Approval requested (id {aid}). This tool needs a tap on "
                       "Approve or Deny in Telegram before it runs.")
            else:
                out = TOOLS[name]["func"](**args)
        except Exception as e:
            out = f"Error: {e}"
        audit.record(_mode, name, args, out)
        history.append({"role": "tool", "tool_call_id": c["id"], "content": str(out)})


def _trim():
    del history[:-MAX_HISTORY]
    while history and history[0]["role"] != "user":
        history.pop(0)


def process_command(text, chat=None):
    if not API_KEY:
        return "Run: export LLM_API_KEY=your-key"
    history.append({"role": "user", "content": text})
    _trim()

    for _ in range(6):
        try:
            limiter.check()
        except limiter.RateLimited as e:
            if history and history[-1]["role"] == "user":
                history.pop()
            return str(e)
        msg = _call()
        entry = {"role": "assistant", "content": msg.get("content") or ""}
        if msg.get("tool_calls"):
            entry["tool_calls"] = msg["tool_calls"]
        history.append(entry)
        if not msg.get("tool_calls"):
            return entry["content"]
        _run_tools(msg, chat)
    return "Too many steps. Try rephrasing."


def process_command_stream(text, emit, chat=None):
    if not API_KEY:
        emit("Run: export LLM_API_KEY=your-key")
        return
    history.append({"role": "user", "content": text})
    _trim()

    for _ in range(6):
        try:
            limiter.check()
        except limiter.RateLimited as e:
            if history and history[-1]["role"] == "user":
                history.pop()
            emit(str(e))
            return
        msg = _call_stream(emit)
        entry = {"role": "assistant", "content": msg.get("content") or ""}
        if msg.get("tool_calls"):
            entry["tool_calls"] = msg["tool_calls"]
        history.append(entry)
        if not msg.get("tool_calls"):
            return
        _run_tools(msg, chat)
    emit("Too many steps. Try rephrasing.")
