import json
import os

DB_FILE = "db.json"

def load_db():
    if not os.path.exists(DB_FILE):
        return {"rss_sources": [], "scrape_sources": [], "sent_news": [], "settings": {}}
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# RSS
def get_rss_sources():
    db = load_db()
    return db.get("rss_sources", [])

def add_rss_source(url):
    db = load_db()
    sources = db.get("rss_sources", [])
    if url not in sources:
        sources.append(url)
        db["rss_sources"] = sources
        save_db(db)

def remove_rss_source(url):
    db = load_db()
    sources = db.get("rss_sources", [])
    if url in sources:
        sources.remove(url)
        db["rss_sources"] = sources
        save_db(db)

# Scraping
def get_scrape_sources():
    db = load_db()
    return db.get("scrape_sources", [])

def add_scrape_source(url):
    db = load_db()
    sources = db.get("scrape_sources", [])
    if url not in sources:
        sources.append(url)
        db["scrape_sources"] = sources
        save_db(db)

def remove_scrape_source(url):
    db = load_db()
    sources = db.get("scrape_sources", [])
    if url in sources:
        sources.remove(url)
        db["scrape_sources"] = sources
        save_db(db)

# Sent news
def is_sent(news_id):
    db = load_db()
    return news_id in db.get("sent_news", [])

def mark_sent(news_id):
    db = load_db()
    sent = db.get("sent_news", [])
    if news_id not in sent:
        sent.append(news_id)
    db["sent_news"] = sent
    save_db(db)

# Settings
def get_setting(key, default=None):
    db = load_db()
    return db.get("settings", {}).get(key, default)

def set_setting(key, value):
    db = load_db()
    settings = db.get("settings", {})
    settings[key] = value
    db["settings"] = settings
    save_db(db)
