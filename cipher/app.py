from cipher.personality import NAME, INTRO
from cipher.core import brain
from cipher.core.memory import get_scope, add_scope, remove_scope

HELP = """/scope add <host>     authorize a host you own
/scope remove <host>
/scope list
/clear               reset conversation
/exit"""


def command(text):
    p = text.split()
    if p[0] == "/help":
        return HELP
    if p[0] == "/clear":
        brain.reset()
        return "Conversation cleared."
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
            text = input("\nYou: ").strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n{NAME}: Goodbye.")
            break
        if not text:
            continue
        if text in ("/exit", "exit", "quit"):
            print(f"\n{NAME}: Goodbye.")
            break
        if text.startswith("/"):
            print(f"\n{command(text)}")
            continue
        try:
            print(f"\n{NAME}: {brain.process_command(text)}")
        except Exception as e:
            print(f"\n{NAME}: Error: {e}")
