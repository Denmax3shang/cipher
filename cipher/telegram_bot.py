import os
import re
import time
import traceback

import requests

from cipher.app import command
from cipher.core import brain

TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
OWNER = os.environ.get("TELEGRAM_OWNER_ID", "")
API = f"https://api.telegram.org/bot{TOKEN}"


def plain(t):
    t = re.sub(r"^\s*\|[\s:\-|]+\|?\s*$", "", t, flags=re.M)
    t = re.sub(r"^\s*-{3,}\s*$", "", t, flags=re.M)
    t = re.sub(r"^\s*\|(.+)\|\s*$",
               lambda m: "- " + " - ".join(c.strip() for c in m.group(1).split("|")),
               t, flags=re.M)
    t = re.sub(r"^```\w*\s*$", "", t, flags=re.M)
    t = re.sub(r"^#{1,6}\s*", "", t, flags=re.M)
    t = re.sub(r"\*\*(.+?)\*\*", r"\1", t)
    t = t.replace("`", "")
    return re.sub(r"\n{3,}", "\n\n", t).strip()


def api(method, **payload):
    return requests.post(f"{API}/{method}", json=payload, timeout=20)


def send(chat, text):
    text = plain(text or "") or "I couldn't produce a reply. Try again."
    for i in range(0, len(text), 4000):
        api("sendMessage", chat_id=chat, text=text[i:i + 4000])


def run():
    if not TOKEN:
        raise SystemExit("Set TELEGRAM_TOKEN first.")
    print("CIPHER Telegram bot running. Ctrl+C to stop.", flush=True)
    offset = None
    while True:
        try:
            r = requests.get(f"{API}/getUpdates",
                             params={"timeout": 30, "offset": offset}, timeout=40).json()
            for u in r.get("result", []):
                offset = u["update_id"] + 1
                m = u.get("message") or {}
                text, chat = m.get("text"), m.get("chat", {}).get("id")
                sender = str(m.get("from", {}).get("id"))
                if not text or chat is None:
                    continue
                if not OWNER:
                    send(chat, f"Your Telegram ID is {sender}. Set TELEGRAM_OWNER_ID={sender} and restart the bot.")
                    continue
                if sender != OWNER:
                    continue
                try:
                    api("sendChatAction", chat_id=chat, action="typing")
                    reply = command(text) if text.startswith("/") else brain.process_command(text)
                except Exception as e:
                    print(traceback.format_exc(), flush=True)
                    reply = f"Error: {e}"
                send(chat, reply)
        except KeyboardInterrupt:
            raise
        except Exception:
            print(traceback.format_exc(), flush=True)
            time.sleep(5)


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("\nStopped.")
