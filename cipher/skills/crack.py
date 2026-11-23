import hashlib
from pathlib import Path

from cipher.config import DATA_DIR
from cipher.skills import skill

WORDLIST_DIR = DATA_DIR / "wordlists"
ALGOS = {"md5": 32, "sha1": 40, "sha256": 64, "sha512": 128}


def _hash(word, algo):
    return hashlib.new(algo, word.encode()).hexdigest()


@skill("crack_hash",
       "Try to crack a hash (md5, sha1, sha256, sha512) against a wordlist. Only for "
       "hashes the user owns or made themselves, e.g. for CTF practice. wordlist is a "
       "file name in the wordlists folder; defaults to the bundled common list.",
       {"hash": {"type": "string"},
        "algo": {"type": "string", "enum": list(ALGOS)},
        "wordlist": {"type": "string"}},
       ["hash", "algo"])
def crack_hash(hash, algo, wordlist="common.txt"):
    h = hash.strip().lower()
    if algo not in ALGOS:
        return "Unknown algorithm. Use: " + ", ".join(ALGOS)
    if len(h) != ALGOS[algo]:
        return f"That doesn't look like a {algo} hash ({ALGOS[algo]} hex chars expected)."

    path = (WORDLIST_DIR / wordlist).resolve()
    if WORDLIST_DIR.resolve() not in path.parents or not path.is_file():
        avail = ", ".join(p.name for p in WORDLIST_DIR.glob("*.txt")) or "none"
        return f"Wordlist not found. Available: {avail}"

    tried = 0
    with path.open(errors="replace") as f:
        for line in f:
            word = line.rstrip("\n")
            if not word:
                continue
            tried += 1
            if _hash(word, algo) == h:
                return f"Cracked after {tried} attempts: {word}"
    return f"Not found in {tried} words from {wordlist}."


@skill("list_wordlists", "List available wordlists for crack_hash.")
def list_wordlists():
    files = sorted(WORDLIST_DIR.glob("*.txt"))
    if not files:
        return "No wordlists found."
    return "\n".join(f"{p.name} ({sum(1 for _ in p.open(errors='replace'))} words)"
                     for p in files)
