import io
import os
import re
import threading
import time
import traceback

import requests

from cipher.app import command
from cipher.core import brain, scheduler
from cipher.core.memory import voice_on

TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
OWNER = os.environ.get("TELEGRAM_OWNER_ID", "")
CHANNEL = os.environ.get("TELEGRAM_CHANNEL", "")
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
    last = None
    for _ in range(2):
        try:
            return requests.post(f"{API}/{method}", json=payload, timeout=30)
        except requests.RequestException as e:
            last = e
    raise last


def typing(chat):
    try:
        requests.post(f"{API}/sendChatAction",
                      json={"chat_id": chat, "action": "typing"}, timeout=5)
    except requests.RequestException:
        pass


def send(chat, text):
    text = plain(text or "") or "I couldn't produce a reply. Try again."
    for i in range(0, len(text), 4000):
        api("sendMessage", chat_id=chat, text=text[i:i + 4000])


def speak(chat, text):
    try:
        from gtts import gTTS
        clean = re.sub(r"[^\w\s.,!?'\-:;()%/@#]", "", text)
        clean = re.sub(r"\s+", " ", clean).strip()[:600]
        if not clean:
            return
        buf = io.BytesIO()
        gTTS(clean, lang="en").write_to_fp(buf)
        buf.seek(0)
        r = requests.post(f"{API}/sendVoice", data={"chat_id": chat},
                          files={"voice": ("cipher.mp3", buf)}, timeout=60)
        print("voice:", r.status_code, r.text[:200], flush=True)
        if not r.ok:
            buf.seek(0)
            r = requests.post(f"{API}/sendAudio", data={"chat_id": chat, "title": "CIPHER"},
                              files={"audio": ("cipher.mp3", buf)}, timeout=60)
            print("audio:", r.status_code, r.text[:200], flush=True)
    except Exception:
        print(traceback.format_exc(), flush=True)


def scheduler_loop():
    while True:
        try:
            for p in scheduler.due_posts():
                if OWNER:
                    send(OWNER, f"📱 Time to post!\n\n{p['text']}")
                scheduler.mark_sent(p["id"])
                if CHANNEL:
                    try:
                        send(CHANNEL, p["text"])
                    except Exception:
                        print(traceback.format_exc(), flush=True)
        except Exception:
            print(traceback.format_exc(), flush=True)
        time.sleep(20)


def run():
    if not TOKEN:
        raise SystemExit("Set TELEGRAM_TOKEN first.")
    print("CIPHER Telegram bot running. Ctrl+C to stop.", flush=True)
    threading.Thread(target=scheduler_loop, daemon=True).start()
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
                is_cmd = text.startswith("/")
                try:
                    typing(chat)
                    reply = command(text) if is_cmd else brain.process_command(text)
                except Exception as e:
                    print(traceback.format_exc(), flush=True)
                    reply = f"Error: {e}"
                send(chat, reply)
                if not is_cmd and voice_on():
                    speak(chat, reply)
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
