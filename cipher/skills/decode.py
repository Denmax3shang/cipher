import base64
import codecs
import json
import re
import string
from datetime import datetime, timezone
from urllib.parse import quote, unquote

from cipher.skills import skill

METHODS = ["base64", "base32", "hex", "url", "rot13", "binary"]
PRINTABLE = set(string.printable)
COMMON = "etaoinshrdlu"


def _readable(raw):
    try:
        s = raw.decode("utf-8")
    except UnicodeDecodeError:
        return None
    if s and sum(c in PRINTABLE for c in s) / len(s) > 0.95:
        return s
    return None


def _englishy(s):
    letters = [c for c in s.lower() if c.isalpha()]
    return len(letters) >= 4 and sum(c in COMMON for c in letters) / len(letters) > 0.65


def _decode(text, method):
    t = text.strip()
    if method == "base64":
        t = re.sub(r"\s+", "", t).replace("-", "+").replace("_", "/")
        return base64.b64decode(t + "=" * (-len(t) % 4), validate=True)
    if method == "base32":
        t = re.sub(r"\s+", "", t).upper()
        return base64.b32decode(t + "=" * (-len(t) % 8))
    if method == "hex":
        return bytes.fromhex(re.sub(r"(0x|\s|:)", "", t))
    if method == "url":
        return unquote(t).encode()
    if method == "rot13":
        return codecs.decode(t, "rot_13").encode()
    if method == "binary":
        bits = re.sub(r"\s", "", t)
        if not re.fullmatch(r"[01]+", bits) or len(bits) % 8:
            raise ValueError("not 8-bit binary")
        return bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits), 8))
    raise ValueError("unknown method")


def _encode(text, method):
    raw = text.encode()
    if method == "base64":
        return base64.b64encode(raw).decode()
    if method == "base32":
        return base64.b32encode(raw).decode()
    if method == "hex":
        return raw.hex()
    if method == "url":
        return quote(text, safe="")
    if method == "rot13":
        return codecs.encode(text, "rot_13")
    if method == "binary":
        return " ".join(f"{b:08b}" for b in raw)
    raise ValueError("unknown method")


@skill("encode_decode",
       "Encode or decode text. method: base64, base32, hex, url, rot13 or binary. "
       "action: encode or decode (default decode).",
       {"text": {"type": "string"},
        "method": {"type": "string", "enum": METHODS},
        "action": {"type": "string", "enum": ["encode", "decode"]}},
       ["text", "method"])
def encode_decode(text, method, action="decode"):
    if method not in METHODS:
        return "Unknown method. Use: " + ", ".join(METHODS)
    try:
        if action == "encode":
            return _encode(text, method)
        raw = _decode(text, method)
    except Exception as e:
        return f"Could not {action} as {method}: {e}"
    return _readable(raw) or f"Decoded to non-text bytes (hex): {raw[:64].hex()}"


@skill("auto_decode",
       "Try common encodings (base64, base32, hex, url, rot13, binary) on a string and "
       "show which give readable text. Good for CTF challenges.",
       {"text": {"type": "string"}}, ["text"])
def auto_decode(text):
    hits = []
    for m in METHODS:
        try:
            s = _readable(_decode(text, m))
        except Exception:
            continue
        if not s or s.strip() == text.strip():
            continue
        if m == "rot13" and not _englishy(s):
            continue
        hits.append(f"{m}: {s[:200]}")
    return "\n".join(hits) or "No common encoding produced readable text."


def _shift(s, k):
    out = []
    for c in s:
        if c.isalpha():
            base = ord("A") if c.isupper() else ord("a")
            out.append(chr((ord(c) - base + k) % 26 + base))
        else:
            out.append(c)
    return "".join(out)


def _score(s):
    letters = [c for c in s.lower() if c.isalpha()]
    return sum(c in COMMON for c in letters) / len(letters) if letters else 0


@skill("caesar_brute",
       "Try every Caesar cipher shift and show the 3 most English-looking results.",
       {"text": {"type": "string"}}, ["text"])
def caesar_brute(text):
    best = sorted(((_score(_shift(text, k)), k) for k in range(1, 26)), reverse=True)[:3]
    return "\n".join(f"shift +{k}: {_shift(text, k)[:200]}" for _, k in best)


def _part(p):
    return json.loads(base64.urlsafe_b64decode(p + "=" * (-len(p) % 4)))


@skill("jwt_decode",
       "Decode a JWT header and payload WITHOUT verifying the signature, and flag "
       "common weaknesses.",
       {"token": {"type": "string"}}, ["token"])
def jwt_decode(token):
    parts = token.strip().split(".")
    if len(parts) != 3:
        return "Not a JWT: expected three dot-separated parts."
    try:
        header, payload = _part(parts[0]), _part(parts[1])
    except Exception as e:
        return f"Could not decode token: {e}"
    out = ["Header: " + json.dumps(header), "Payload: " + json.dumps(payload)]
    notes = []
    alg = str(header.get("alg", "")).lower()
    if alg == "none" or not parts[2]:
        notes.append("unsigned token (alg none or empty signature)")
    elif alg.startswith("hs"):
        notes.append("HMAC-signed: a weak secret can be brute-forced offline")
    for key in ("iat", "nbf", "exp"):
        v = payload.get(key)
        if isinstance(v, (int, float)):
            when = datetime.fromtimestamp(v, timezone.utc)
            out.append(f"{key}: {when:%Y-%m-%d %H:%M} UTC")
            if key == "exp" and when < datetime.now(timezone.utc):
                notes.append("token is expired")
    if "exp" not in payload:
        notes.append("no exp claim, so it never expires")
    out.append("Signature NOT verified.")
    if notes:
        out.append("Findings: " + "; ".join(notes))
    return "\n".join(out)
