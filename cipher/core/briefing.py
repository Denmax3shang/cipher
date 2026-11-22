from datetime import datetime, timedelta

from cipher.core import audit, memory, scheduler
from cipher.skills.weather import get_weather

DEFAULTS = {"on": False, "time": "07:30", "city": "", "last_sent": ""}
USAGE = "Usage: /briefing | /briefing on | off | time HH:MM | city NAME | settings"

TIPS = [
    "Use a password manager and a unique password for every account.",
    "Turn on two-factor authentication, preferably an authenticator app or security key instead of SMS.",
    "Update your phone and apps: most real attacks use bugs that already have patches.",
    "Your email password resets every other account, so never reuse it anywhere.",
    "Rotate any API key or token the moment it appears in a screenshot, chat, or log.",
    "Back up important files with the 3-2-1 rule: 3 copies, 2 media types, 1 offsite.",
    "Press and hold a link to preview it before opening. Phishing relies on rushing you.",
    "Prefer a passphrase of four or more random words over a short complex password.",
    "Set a PIN on your SIM card to make SIM-swap attacks harder.",
    "Review app permissions: does a flashlight app need your contacts?",
    "Check haveibeenpwned.com now and then to see if your email appeared in a breach.",
    "Only scan or test systems you own or have written permission to test.",
]


def load():
    return {**DEFAULTS, **memory.load_json("briefing.json", {})}


def save(cfg):
    memory.save_json("briefing.json", cfg)


def build(now=None):
    now = now or datetime.now()
    cfg = load()
    today = now.strftime("%Y-%m-%d")
    greet = "Good morning" if now.hour < 12 else "Good afternoon" if now.hour < 18 else "Good evening"
    lines = [f"☀️ {greet}! {now:%A, %d %B %Y}", ""]

    if cfg["city"]:
        lines.append("🌤️ " + get_weather(cfg["city"]))
    else:
        lines.append("🌤️ Set your city for weather: /briefing city YOUR_CITY")

    posts = [p for p in scheduler.list_posts() if p["when"].startswith(today)]
    lines += ["", "📱 Posts today:"]
    if posts:
        lines += [f"- {p['when'][11:]} {p['text'][:60]}" for p in posts]
    else:
        lines.append("- none scheduled")

    notes = memory.load_json("notes.json", [])
    lines += ["", f"📝 Notes: {len(notes)} saved"]
    lines += [f"- {n[:70]}" for n in notes[-3:]]

    recent = audit.recent(24)
    blocked = sum(e["status"] == "blocked" for e in recent)
    lines += ["", f"🛡️ Last 24h: {len(recent)} tool calls, {blocked} blocked"]
    lines += ["", "💡 Tip: " + TIPS[now.timetuple().tm_yday % len(TIPS)]]
    return "\n".join(lines)


def due(now=None):
    now = now or datetime.now()
    cfg = load()
    today = now.strftime("%Y-%m-%d")
    if not cfg["on"] or cfg["last_sent"] == today:
        return False
    start = datetime.strptime(f"{today} {cfg['time']}", "%Y-%m-%d %H:%M")
    return start <= now <= start + timedelta(hours=3)


def mark_sent(now=None):
    cfg = load()
    cfg["last_sent"] = (now or datetime.now()).strftime("%Y-%m-%d")
    save(cfg)


def handle(args):
    if not args:
        return build()
    cfg = load()
    cmd = args[0].lower()
    if cmd in ("on", "off"):
        cfg["on"] = cmd == "on"
        save(cfg)
        if cfg["on"]:
            return (f"☀️ Daily briefing on at {cfg['time']}. "
                    "It is sent only while the Telegram bot is running.")
        return "Daily briefing off."
    if cmd == "time" and len(args) == 2:
        try:
            cfg["time"] = datetime.strptime(args[1], "%H:%M").strftime("%H:%M")
        except ValueError:
            return "Use 24-hour time like 07:30."
        save(cfg)
        return f"Briefing time set to {cfg['time']}."
    if cmd == "city" and len(args) >= 2:
        cfg["city"] = " ".join(args[1:]).replace("<", "").replace(">", "").strip()
        save(cfg)
        return f"Briefing city set to {cfg['city']}."
    if cmd == "settings":
        return (f"Briefing: {'on' if cfg['on'] else 'off'} at {cfg['time']}\n"
                f"City: {cfg['city'] or 'not set'}")
    return USAGE
