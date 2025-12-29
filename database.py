import json
import os
from datetime import datetime
from pathlib import Path

DB_FILE = Path("collected_news.json")

def save_collected_news(news_list):
    """ذخیره اخبار جمع‌آوری‌شده در فایل"""
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(news_list, f, ensure_ascii=False, indent=2)

def get_collected_news(limit=None):
    """خواندن اخبار جمع‌آوری‌شده واقعی از فایل"""
    if not DB_FILE.exists():
        return []

    with open(DB_FILE, "r", encoding="utf-8") as f:
        news = json.load(f)

    if limit:
        return news[:limit]
    return news
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

# ============ SETTINGS ============
def get_setting(key, default=None):
    s = _load("settings", {})
    return s.get(key, default)

def set_setting(key, value):
    s = _load("settings", {})
    s[key] = value
    _save("settings", s)

# ============ SOURCES (RSS & Scrape) ============
def get_sources():
    """برگرداندن همه منابع"""
    return _load("sources", {"rss": [], "scrape": []})

def get_rss_sources():
    """فقط منابع RSS"""
    data = get_sources()
    return data.get("rss", [])

def get_scrape_sources():
    """فقط منابع Scrape"""
    data = get_sources()
    return data.get("scrape", [])

def add_rss_source(url):
    """افزودن RSS"""
    data = get_sources()
    if url not in data["rss"]:
        data["rss"].append(url)
        _save("sources", data)

def add_scrape_source(url):
    """افزودن Scrape"""
    data = get_sources()
    if url not in data["scrape"]:
        data["scrape"].append(url)
        _save("sources", data)

def remove_rss_source(url):
    """حذف RSS"""
    data = get_sources()
    if url in data["rss"]:
        data["rss"].remove(url)
        _save("sources", data)

def remove_scrape_source(url):
    """حذف Scrape"""
    data = get_sources()
    if url in data["scrape"]:
        data["scrape"].remove(url)
        _save("sources", data)

# ============ SENT ============
def is_sent(uid):
    return uid in _load("sent", [])

def mark_sent(uid):
    data = _load("sent", [])
    if uid not in data:
        data.append(uid)
        _save("sent", data)

# ============ TOPICS (for trends) ============
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
