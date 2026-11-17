from datetime import datetime
from cipher.skills import skill
from cipher.core.memory import load_json, save_json, add_fact


@skill("get_time", "Get the current local date and time.")
def get_time():
    return datetime.now().strftime("%A, %d %B %Y, %H:%M")


@skill("remember", "Store a lasting fact about the user.",
       {"fact": {"type": "string"}}, ["fact"])
def remember(fact):
    add_fact(fact)
    return "Remembered."


@skill("add_note", "Save a note or finding.",
       {"text": {"type": "string"}}, ["text"])
def add_note(text):
    notes = load_json("notes.json", [])
    notes.append(f"[{datetime.now():%Y-%m-%d %H:%M}] {text}")
    save_json("notes.json", notes)
    return f"Saved note #{len(notes)}."


@skill("list_notes", "List all saved notes.")
def list_notes():
    notes = load_json("notes.json", [])
    return "\n".join(f"{i}. {n}" for i, n in enumerate(notes, 1)) or "No notes yet."
