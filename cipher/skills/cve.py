import re

import requests

from cipher.skills import skill

NVD = "https://services.nvd.nist.gov/rest/json/cves/2.0"
HEADERS = {"User-Agent": "CIPHER/0.1 (personal assistant)"}


def _score(cve):
    metrics = cve.get("metrics", {})
    for key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
        if metrics.get(key):
            m = metrics[key][0]
            data = m["cvssData"]
            sev = data.get("baseSeverity") or m.get("baseSeverity", "?")
            return float(data["baseScore"]), sev
    return 0.0, "N/A"


def _desc(cve, limit):
    for d in cve.get("descriptions", []):
        if d.get("lang") == "en":
            return d["value"].replace("\n", " ")[:limit]
    return "No description."


@skill("cve_lookup",
       "Look up known vulnerabilities (CVEs) in the NVD database. Pass a CVE ID "
       "like CVE-2021-44228, or a product and version like 'OpenSSH 8.9'.",
       {"query": {"type": "string"}}, ["query"])
def cve_lookup(query):
    q = query.strip()
    by_id = re.fullmatch(r"(?i)CVE-\d{4}-\d{4,}", q)
    params = {"cveId": q.upper()} if by_id else {"keywordSearch": q, "resultsPerPage": 20}
    try:
        r = requests.get(NVD, params=params, headers=HEADERS, timeout=20)
        if r.status_code in (403, 429):
            return "NVD is rate limiting requests. Wait 30 seconds and try again."
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        return f"NVD lookup failed: {e}"

    items = [v["cve"] for v in data.get("vulnerabilities", [])]
    if not items:
        return "No CVEs found for that query."
    items.sort(key=lambda c: _score(c)[0], reverse=True)

    lines = [f"Found {data.get('totalResults', len(items))} CVEs. Top by severity:"]
    for c in items[:5]:
        score, sev = _score(c)
        lines.append(f"{c['id']} | {score} {sev} | {c.get('published', '')[:10]} | "
                     f"{_desc(c, 600 if by_id else 200)}")
    lines.append("Note: keyword search matches text, so check affected versions yourself.")
    return "\n".join(lines)
