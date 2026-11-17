import json
import os
from cipher.config import DATA_DIR


def load_json(name, default):
    try:
        return json.loads((DATA_DIR / name).read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def save_json(name, data):
    path = DATA_DIR / name
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2))
    os.replace(tmp, path)


def get_facts():
    return load_json("memory.json", {"facts": []})["facts"]


def add_fact(fact):
    data = load_json("memory.json", {"facts": []})
    if fact not in data["facts"]:
        data["facts"].append(fact)
        save_json("memory.json", data)


def get_scope():
    return load_json("scope.json", [])


def add_scope(host):
    s = get_scope()
    host = host.lower().strip()
    if host not in s:
        s.append(host)
        save_json("scope.json", s)


def remove_scope(host):
    save_json("scope.json", [h for h in get_scope() if h != host.lower().strip()])


def in_scope(host):
    host = host.lower().strip()
    return host in ("localhost", "127.0.0.1") or host in get_scope()
