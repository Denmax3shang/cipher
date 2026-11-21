import io
import os
import re
import threading
import time
import traceback

import requests

from cipher.app import command
from cipher.config import API_KEY, BASE_URL
from cipher.core import brain, scheduler
from cipher.core.memory import voice_on

TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
OWNER = os.environ.get("TELEGRAM_OWNER_ID", "")
CHANNEL = os.environ.get("TELEGRAM_CHANNEL", "")
STT_MODEL = os.environ.get("STT_MODEL", "whisper-large-v3-turbo")
API = f"https://api.telegram.org/bot{TOKEN}"


def redact(s):
    for secret in (TOKEN, API_KEY):
        if secret:
            s = s.replace(secret, "***")
    return s


def log_error():
    print(redact(traceback.format_exc()), flush=True)


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


def transcribe(file_id):
    info = requests.get(f"{API}/getFile", params={"file_id": file_id}, timeout=20).json()
    path = info["result"]["file_path"]
    audio = requests.get(f"https://api.telegram.org/file/bot{TOKEN}/{path}",
                         timeout=60).content
    r = requests.post(f"{BASE_URL}/audio/transcriptions",
                      headers={"Authorization": f"Bearer {API_KEY}"},
                      data={"model": STT_MODEL, "response_format": "text"},
                      files={"file": ("voice.ogg", audio)}, timeout=60)
    if not r.ok:
        raise RuntimeError(f"{r.status_code}: {r.text[:200]}")
    return r.text.strip()


def speakable(text):
    return 0 < len(text) <= 600 and text.count("\n") <= 6


def speak(chat, text):
    try:
        from gtts import gTTS
        clean = re.sub(r"[^\w\s.,!?'\-:;()%/@#]", "", text)
        clean = re.sub(r"\s+", " ", clean).strip()
        if not clean:
            return False
        buf = io.BytesIO()
        gTTS(clean, lang="en").write_to_fp(buf)
        buf.seek(0)
        r = requests.post(f"{API}/sendVoice", data={"chat_id": chat},
                          files={"voice": ("cipher.mp3", buf)}, timeout=60)
        if r.ok:
            return True
        buf.seek(0)
        r = requests.post(f"{API}/sendAudio", data={"chat_id": chat, "title": "CIPHER"},
                          files={"audio": ("cipher.mp3", buf)}, timeout=60)
        return r.ok
    except Exception:
        log_error()
        return False


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
                        log_error()
        except Exception:
            log_error()
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
                media = m.get("voice") or m.get("audio")
                sender = str(m.get("from", {}).get("id"))
                if chat is None or not (text or media):
                    continue
                if not OWNER:
                    send(chat, f"Your Telegram ID is {sender}. Set TELEGRAM_OWNER_ID={sender} and restart the bot.")
                    continue
                if sender != OWNER:
                    continue

                heard = False
                if not text:
                    try:
                        typing(chat)
                        text = transcribe(media["file_id"])
                    except Exception as e:
                        log_error()
                        send(chat, f"Couldn't process that voice note: {redact(str(e))}")
                        continue
                    if not text:
                        send(chat, "I couldn't hear anything in that voice note 🎙️")
                        continue
                    send(chat, f"🎙️ I heard: {text}")
                    heard = True

                is_cmd = text.startswith("/") and not heard
                try:
                    typing(chat)
                    reply = command(text) if is_cmd else brain.process_command(text)
                except Exception as e:
                    log_error()
                    reply = f"Error: {redact(str(e))}"
                if (not is_cmd and (heard or voice_on())
                        and speakable(plain(reply)) and speak(chat, plain(reply))):
                    continue
                send(chat, reply)
        except KeyboardInterrupt:
            raise
        except Exception:
            log_error()
            time.sleep(5)


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("\nStopped.")
