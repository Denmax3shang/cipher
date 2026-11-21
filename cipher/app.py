from cipher.personality import NAME, INTRO, MODES
from cipher.core import audit, brain
from cipher.core.report import make_export, status
from cipher.core.memory import get_scope, add_scope, remove_scope, voice_on, set_voice

HELP = """/mode security | social | chill | research
/scope add HOST | remove HOST | list
/voice on | off   Telegram voice replies
/status  system overview
/audit [n]  recent tool activity
/export  save notes, facts and chat
/clear  reset conversation
/exit   quit"""


def command(text):
    p = text.split()
    if p[0] == "/help":
        return HELP
    if p[0] == "/clear":
        brain.reset()
        return "Conversation cleared. ✨"
    if p[0] == "/mode":
        if len(p) == 2:
            name = p[1].lower()
            if brain.set_mode(name):
                return f"{MODES[name]['emoji']} Mode: {name}"
            return "Unknown mode. Options: " + ", ".join(MODES)
        cur = brain.get_mode()
        return f"{MODES[cur]['emoji']} Current mode: {cur}. Options: " + ", ".join(MODES)
    if p[0] == "/status":
        return status()
    if p[0] == "/audit":
        n = int(p[1]) if len(p) == 2 and p[1].isdigit() else 10
        return audit.tail(min(n, 30))
    if p[0] == "/export":
        return f"Saved: {make_export()}"
    if p[0] == "/voice":
        if len(p) == 2 and p[1] in ("on", "off"):
            set_voice(p[1] == "on")
            return "🔊 Voice replies on (Telegram only)" if p[1] == "on" else "🔇 Voice replies off"
        return "Voice is " + ("on" if voice_on() else "off") + ". Use /voice on or /voice off"
    if p[0] == "/scope":
        if len(p) == 3 and p[1] == "add":
            add_scope(p[2])
            return f"Added {p[2]} to scope."
        if len(p) == 3 and p[1] == "remove":
            remove_scope(p[2])
            return f"Removed {p[2]}."
        return "Scope: " + (", ".join(get_scope()) or "empty (only localhost allowed)")
    return "Unknown command. /help"


def run():
    print("=" * 40 + f"\n{NAME:^40}\n" + "=" * 40)
    print(f"\n{INTRO}")
    while True:
        try:
            text = input(f"\nYou [{brain.get_mode()}]: ").strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n{NAME}: Goodbye.")
            break
        if not text:
            continue
        if text in ("/exit", "exit", "quit"):
            print(f"\n{NAME}: Goodbye. 👋")
            break
        if text.startswith("/"):
            print(f"\n{command(text)}")
            continue
        try:
            print(f"\n{NAME}: {brain.process_command(text)}")
        except Exception as e:
            print(f"\n{NAME}: Error: {e}")
