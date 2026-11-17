import re
from collections import Counter
from urllib.parse import unquote_plus

from cipher.config import DATA_DIR
from cipher.skills import skill

LOG_DIR = DATA_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

FAILED = re.compile(r"Failed (?:password|publickey) for (?:invalid user )?(\S+) from ([\d.]+)")
ACCEPTED = re.compile(r"Accepted (\S+) for (\S+) from ([\d.]+)")
WEB = re.compile(r'^([\d.]+) \S+ \S+ \[[^\]]*\] "\S+ (\S+)[^"]*" (\d{3})')
BAD = ("../", "/etc/passwd", "union select", "<script", "/.env", "wp-login",
       "phpmyadmin", "/.git", "cmd=", "${jndi", "/bin/sh")


def _top(counter, n=5):
    return ", ".join(f"{k} ({v})" for k, v in counter.most_common(n))


@skill("analyze_log",
       "Analyze an SSH auth log or web access log from the logs folder and report "
       "suspicious activity. Pass only the file name.",
       {"filename": {"type": "string"}}, ["filename"])
def analyze_log(filename):
    path = (LOG_DIR / filename).resolve()
    if LOG_DIR.resolve() not in path.parents or not path.is_file():
        return f"File not found. Put logs in {LOG_DIR} and pass only the file name."

    fails, users, web_err, web_bad, codes = (Counter() for _ in range(5))
    logins, n = [], 0
    with path.open(errors="replace") as f:
        for line in f:
            n += 1
            if n > 200000:
                break
            if m := FAILED.search(line):
                users[m[1]] += 1
                fails[m[2]] += 1
            elif m := ACCEPTED.search(line):
                logins.append((m[2], m[3], m[1], fails[m[3]]))
            elif m := WEB.search(line):
                ip, target, code = m[1], unquote_plus(m[2]).lower(), m[3]
                codes[code] += 1
                if code in ("401", "403"):
                    web_err[ip] += 1
                if any(b in target for b in BAD):
                    web_bad[ip] += 1

    out = [f"Lines read: {n}"]
    if fails:
        out.append(f"Failed SSH logins: {sum(fails.values())}")
        out.append(f"Top attacker IPs: {_top(fails)}")
        out.append(f"Usernames targeted: {_top(users)}")
    for user, ip, method, prior in logins:
        if prior >= 5:
            out.append(f"ALERT: {ip} failed {prior} times, then logged in as {user} ({method})")
    if codes:
        out.append(f"HTTP status counts: {_top(codes, 6)}")
    if web_err:
        out.append(f"IPs with many 401/403: {_top(web_err)}")
    if web_bad:
        out.append(f"IPs sending attack-like requests: {_top(web_bad)}")
    return "\n".join(out) if len(out) > 1 else "No suspicious activity found."
