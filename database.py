import json
import os
from datetime import datetime

BASE = "data"
os.makedirs(BASE, exist_ok=True)

FILES = {
    "settings": f"{BASE}/settings.json",
    "sources": f"{BASE}/sources.json",
    "sent": f"{BASE}/sent.json",
    "topics": f"{BASE}/topics.json"
}

def _load(name, default):
    if not os.path.exists(FILES[name]):
        with open(FILES[name], "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False)
    with open(FILES[name], encoding="utf-8") as f:
        return json.load(f)

def _save(name, data):
    with open(FILES[name], "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# SETTINGS
def get_setting(key, default=None):
    s = _load("settings", {})
    return s.get(key, default)

def set_setting(key, value):
    s = _load("settings", {})
    s[key] = value
    _save("settings", s)

# SOURCES
def get_sources():
    return _load("sources", [])

def add_source(src):
    data = _load("sources", [])
    data.append(src)
    _save("sources", data)

def remove_source(index):
    data = _load("sources", [])
    data.pop(index)
    _save("sources", data)

# SENT
def is_sent(uid):
    return uid in _load("sent", [])

def mark_sent(uid):
    data = _load("sent", [])
    data.append(uid)
    _save("sent", data)

# TOPICS (for trends)
def save_topic(topic, source):
    data = _load("topics", [])
    today = datetime.utcnow().date().isoformat()
    data.append({"topic": topic, "source": source, "date": today})
    _save("topics", data)

def daily_trends():
    data = _load("topics", [])
    today = datetime.utcnow().date().isoformat()
    count = {}
    for i in data:
        if i["date"] == today:
            count.setdefault(i["topic"], set()).add(i["source"])
    return [k for k, v in count.items() if len(v) >= 3]
