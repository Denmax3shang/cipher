import os
import time

import requests

from cipher.app import command
from cipher.core import brain

TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
OWNER = os.environ.get("TELEGRAM_OWNER_ID", "")
API = f"https://api.telegram.org/bot{TOKEN}"


def send(chat, text):
    text = text or "(empty reply)"
    for i in range(0, len(text), 4000):
        requests.post(f"{API}/sendMessage",
                      json={"chat_id": chat, "text": text[i:i + 4000]}, timeout=20)


def run():
    if not TOKEN:
        raise SystemExit("Set TELEGRAM_TOKEN first.")
    print("CIPHER Telegram bot running. Ctrl+C to stop.")
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
                    reply = command(text) if text.startswith("/") else brain.process_command(text)
                except Exception as e:
                    reply = f"Error: {e}"
                send(chat, reply)
        except KeyboardInterrupt:
            raise
        except Exception:
            time.sleep(5)


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("\nStopped.")
