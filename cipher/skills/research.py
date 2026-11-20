from urllib.parse import quote

import requests

from cipher.skills import skill

HEADERS = {"User-Agent": "CIPHER/0.1 (personal assistant)"}


@skill("wiki_search", "Look up a topic on Wikipedia and return a short summary.",
       {"topic": {"type": "string"}}, ["topic"])
def wiki_search(topic):
    try:
        r = requests.get("https://en.wikipedia.org/w/api.php",
                         params={"action": "query", "list": "search", "srsearch": topic,
                                 "format": "json", "srlimit": 1},
                         headers=HEADERS, timeout=15).json()
        hits = r["query"]["search"]
        if not hits:
            return "No Wikipedia article found."
        title = hits[0]["title"]
        s = requests.get("https://en.wikipedia.org/api/rest_v1/page/summary/"
                         + quote(title.replace(" ", "_"), safe=""),
                         headers=HEADERS, timeout=15).json()
        url = s.get("content_urls", {}).get("desktop", {}).get("page", "")
        return f"{s.get('title', title)}: {s.get('extract', 'No summary.')[:1500]}\nSource: {url}"
    except Exception as e:
        return f"Lookup failed: {e}"
