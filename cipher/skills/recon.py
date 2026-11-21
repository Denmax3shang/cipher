import re
import socket
import ssl
from datetime import datetime, timezone

import requests

from cipher.skills import skill
from cipher.skills.security import _blocked

UA = {"User-Agent": "CIPHER/0.1 (personal assistant)"}
DOMAIN = re.compile(r"[a-z0-9.-]+\.[a-z]{2,}")


def _whois_query(server, query):
    with socket.create_connection((server, 43), timeout=10) as s:
        s.sendall((query + "\r\n").encode())
        data = b""
        while chunk := s.recv(4096):
            data += chunk
    return data.decode(errors="replace")


@skill("whois_lookup", "WHOIS lookup for a domain name (public registry data).",
       {"domain": {"type": "string"}}, ["domain"])
def whois_lookup(domain):
    domain = domain.strip().lower()
    if not DOMAIN.fullmatch(domain):
        return "That doesn't look like a valid domain."
    try:
        iana = _whois_query("whois.iana.org", domain.rsplit(".", 1)[-1])
        m = re.search(r"^(?:refer|whois):\s*(\S+)", iana, re.M | re.I)
        if not m:
            return "No WHOIS server found for that TLD."
        raw = _whois_query(m.group(1), domain)
    except Exception as e:
        return f"WHOIS failed: {e}"
    keys = ("domain name", "registrar:", "creation date", "created", "expir",
            "updated date", "name server", "nserver", "status")
    seen, lines = set(), []
    for line in raw.splitlines():
        s = line.strip()
        if s and any(k in s.lower() for k in keys) and s not in seen:
            seen.add(s)
            lines.append(s)
    return "\n".join(lines[:14]) or raw[:800]


@skill("subdomain_lookup",
       "List subdomains of a domain seen in public certificate transparency logs "
       "(passive, uses crt.sh).",
       {"domain": {"type": "string"}}, ["domain"])
def subdomain_lookup(domain):
    domain = domain.strip().lower()
    if not DOMAIN.fullmatch(domain):
        return "That doesn't look like a valid domain."
    try:
        r = requests.get("https://crt.sh/", headers=UA, timeout=30,
                         params={"q": f"%.{domain}", "output": "json"})
        r.raise_for_status()
        names = set()
        for row in r.json():
            for n in row["name_value"].split("\n"):
                n = n.strip().lower().lstrip("*.")
                if (n == domain or n.endswith("." + domain)) and "@" not in n:
                    names.add(n)
    except Exception as e:
        return f"crt.sh lookup failed (it is often slow or busy): {e}"
    if not names:
        return "No subdomains found."
    out = sorted(names)
    return f"{len(out)} names found. First 40:\n" + "\n".join(out[:40])


@skill("ssl_check",
       "Check a host's TLS certificate: issuer, expiry, names, TLS version. "
       "Only works on in-scope hosts.",
       {"host": {"type": "string"}, "port": {"type": "integer"}}, ["host"])
def ssl_check(host, port=443):
    if not in_scope_host(host):
        return _blocked(host)
    ctx = ssl.create_default_context()
    try:
        with socket.create_connection((host, int(port)), timeout=10) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as tls:
                cert, version, cipher = tls.getpeercert(), tls.version(), tls.cipher()[0]
    except ssl.SSLCertVerificationError as e:
        return f"Certificate verification FAILED: {e.verify_message}"
    except Exception as e:
        return f"Connection failed: {e}"
    exp = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
    days = (exp - datetime.now(timezone.utc)).days
    subject = dict(x[0] for x in cert["subject"]).get("commonName", "?")
    issuer = dict(x[0] for x in cert["issuer"]).get("organizationName", "?")
    sans = [v for k, v in cert.get("subjectAltName", []) if k == "DNS"]
    warn = " ⚠️ expiring soon" if days < 30 else ""
    return (f"Valid certificate for {subject}\nIssuer: {issuer}\n"
            f"Expires: {exp:%Y-%m-%d} ({days} days){warn}\n"
            f"TLS: {version}, cipher {cipher}\nNames: {', '.join(sans[:8])}")


def in_scope_host(host):
    from cipher.core.memory import in_scope
    return in_scope(host)
