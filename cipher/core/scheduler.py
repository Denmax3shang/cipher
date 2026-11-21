import threading
import uuid
from datetime import datetime

from cipher.core.memory import load_json, save_json

_lock = threading.Lock()
FMT = "%Y-%m-%d %H:%M"


def add_post(text, when):
    dt = datetime.strptime(when.strip(), FMT)
    if dt <= datetime.now():
        raise ValueError("that time is in the past")
    with _lock:
        posts = load_json("posts.json", [])
        post = {"id": uuid.uuid4().hex[:4], "text": text,
                "when": dt.strftime(FMT), "sent": False}
        posts.append(post)
        save_json("posts.json", posts)
    return post


def list_posts():
    with _lock:
        return [p for p in load_json("posts.json", []) if not p["sent"]]


def cancel_post(pid):
    with _lock:
        posts = load_json("posts.json", [])
        keep = [p for p in posts if p["id"] != pid]
        save_json("posts.json", keep)
        return len(keep) < len(posts)


def due_posts():
    now = datetime.now().strftime(FMT)
    with _lock:
        return [p for p in load_json("posts.json", [])
                if not p["sent"] and p["when"] <= now]


def mark_sent(pid):
    with _lock:
        posts = load_json("posts.json", [])
        for p in posts:
            if p["id"] == pid:
                p["sent"] = True
        save_json("posts.json", posts)
