import hashlib
import math
import re
import secrets
import socket
import string
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

from cipher.skills import skill
from cipher.core.memory import in_scope


def _blocked(host):
    return (f"BLOCKED: {host} is not in scope. The user must run "
            f"/scope add {host} after confirming they own it or have written authorization.")


@skill("hash_identify", "Guess the type of a hash string from its format and length.",
       {"hash": {"type": "string"}}, ["hash"])
def hash_identify(hash):
    h = hash.strip()
    if re.match(r"^\$2[aby]\$", h):
        return "bcrypt"
    if h.startswith("$argon2"):
        return "Argon2"
    if h.startswith("$6$"):
        return "SHA-512 crypt"
    if h.startswith("$5$"):
        return "SHA-256 crypt"
    if h.startswith("$1$"):
        return "MD5 crypt"
    if re.fullmatch(r"[a-fA-F0-9]+", h):
        types = {32: "MD5 or NTLM", 40: "SHA-1", 56: "SHA-224", 64: "SHA-256",
                 96: "SHA-384", 128: "SHA-512"}
        return types.get(len(h), f"Unknown hex hash ({len(h)} chars)")
    return "Unknown format"


@skill("hash_text", "Hash text with md5, sha1, sha256 or sha512.",
       {"text": {"type": "string"},
        "algo": {"type": "string", "enum": ["md5", "sha1", "sha256", "sha512"]}},
       ["text", "algo"])
def hash_text(text, algo):
    return hashlib.new(algo, text.encode()).hexdigest()


@skill("password_check", "Estimate password strength (entropy in bits).",
       {"password": {"type": "string"}}, ["password"])
def password_check(password):
    pools = [(string.ascii_lowercase, 26), (string.ascii_uppercase, 26),
             (string.digits, 10), (string.punctuation, 32)]
    size = sum(n for chars, n in pools if any(c in chars for c in password))
    bits = len(password) * math.log2(size) if size else 0
    common = {"password", "123456", "qwerty", "letmein", "admin", "welcome"}
    if password.lower() in common:
        return "Very weak: common password."
    verdict = ("weak" if bits < 40 else "okay" if bits < 60
               else "strong" if bits < 80 else "very strong")
    return f"~{bits:.0f} bits, {verdict} (upper bound, ignores patterns)."


@skill("generate_password", "Generate a secure random password.",
       {"length": {"type": "integer"}})
def generate_password(length=20):
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*-_"
    return "".join(secrets.choice(alphabet) for _ in range(max(8, min(int(length), 128))))


@skill("dns_lookup", "Resolve a hostname to IP addresses.",
       {"host": {"type": "string"}}, ["host"])
def dns_lookup(host):
    try:
        return "\n".join(sorted({a[4][0] for a in socket.getaddrinfo(host, None)}))
    except socket.gaierror as e:
        return f"Lookup failed: {e}"


@skill("port_scan", "TCP connect scan of a host. Only works on in-scope hosts. "
       "ports like '22,80,443' or '1-1024' (max 1024 ports).",
       {"host": {"type": "string"}, "ports": {"type": "string"}}, ["host"])
def port_scan(host, ports="1-1024"):
    if not in_scope(host):
        return _blocked(host)
    plist = []
    for part in ports.split(","):
        if "-" in part:
            a, b = part.split("-")
            plist += range(int(a), int(b) + 1)
        else:
            plist.append(int(part))
    plist = [p for p in plist if 0 < p < 65536][:1024]

    def probe(p):
        try:
            socket.create_connection((host, p), timeout=0.6).close()
            return p
        except OSError:
            return None

    with ThreadPoolExecutor(100) as ex:
        found = sorted(p for p in ex.map(probe, plist) if p)
    if not found:
        return f"No open ports found among {len(plist)} scanned."
    out = []
    for p in found:
        try:
            svc = socket.getservbyport(p)
        except OSError:
            svc = "unknown"
        out.append(f"{p}/tcp open {svc}")
    return "\n".join(out)


@skill("http_audit", "Check a URL's security headers. Only works on in-scope hosts.",
       {"url": {"type": "string"}}, ["url"])
def http_audit(url):
    if "://" not in url:
        url = "https://" + url
    host = urlparse(url).hostname or ""
    if not in_scope(host):
        return _blocked(host)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "CIPHER-audit"})
        with urllib.request.urlopen(req, timeout=10) as r:
            headers = {k.lower(): v for k, v in r.headers.items()}
            status = r.status
    except Exception as e:
        return f"Request failed: {e}"
    checks = ["strict-transport-security", "content-security-policy",
              "x-content-type-options", "x-frame-options", "referrer-policy",
              "permissions-policy"]
    lines = [f"HTTP {status}"]
    lines += [f"{'OK     ' if c in headers else 'MISSING'} {c}" for c in checks]
    if "server" in headers:
        lines.append(f"INFO    server: {headers['server']}")
    return "\n".join(lines)
