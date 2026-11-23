import re
from datetime import datetime

from cipher.core import audit
from cipher.skills.recon import whois_lookup, subdomain_lookup, ssl_check

DOMAIN = re.compile(r"[a-z0-9.-]+\.[a-z]{2,}")
COMMON_PORTS = "21,22,23,25,53,80,110,143,443,445,465,587,993,995,3306,3389,5432,8080,8443"


def run(domain, mode="security"):
    domain = domain.strip().lower()
    if not DOMAIN.fullmatch(domain):
        return "That doesn't look like a valid domain."

    from cipher.skills.security import port_scan  # local import avoids a circular import

    lines = [f"🔍 Recon dossier for {domain}", f"Generated {datetime.now():%Y-%m-%d %H:%M}", ""]

    lines.append("WHOIS:")
    out = whois_lookup(domain)
    audit.record(mode, "whois_lookup", {"domain": domain}, out)
    lines.append(out[:800])

    lines.append("\nSubdomains (passive, crt.sh):")
    out = subdomain_lookup(domain)
    audit.record(mode, "subdomain_lookup", {"domain": domain}, out)
    lines.append(out[:1500])

    lines.append(f"\nOpen ports on {domain} (common ports only):")
    out = port_scan(domain, COMMON_PORTS)
    audit.record(mode, "port_scan", {"host": domain, "ports": COMMON_PORTS}, out)
    lines.append(out)

    lines.append(f"\nTLS certificate on {domain}:")
    out = ssl_check(domain)
    audit.record(mode, "ssl_check", {"host": domain}, out)
    lines.append(out)

    lines.append("\nNote: WHOIS and subdomains are passive public records. The port "
                 "scan and TLS check actively connect to the host, so they only run "
                 "if the domain is in your scope (/scope add).")
    return "\n".join(lines)
