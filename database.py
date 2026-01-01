import json
import os
from datetime import datetime
from pathlib import Path

BASE = "data"
os.makedirs(BASE, exist_ok=True)

FILES = {
    "settings": f"{BASE}/settings.json",
    "sources": f"{BASE}/sources.json",
    "sent": f"{BASE}/sent.json",
    "topics": f"{BASE}/topics.json",
    "collected_news": f"{BASE}/collected_news.json"
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
def save_topic(topic, link, source, date):
    """ذخیره topic برای تحلیل ترند"""
    data = _load("topics", [])
    data.append({
        "topic": topic,
        "link": link,
        "source": source,
        "date": date
    })
    _save("topics", data)

def daily_trends(date=None):
    """دریافت ترندهای یک روز خاص"""
    if date is None:
        date = datetime.utcnow().date().isoformat()
    
    data = _load("topics", [])
    count = {}
    
    for item in data:
        if item["date"] == date:
            topic = item["topic"]
            source = item["source"]
            
            if topic not in count:
                count[topic] = {"sources": set(), "links": []}
            
            count[topic]["sources"].add(source)
            count[topic]["links"].append(item.get("link", ""))
    
    # فقط اخباری که از 2 منبع یا بیشتر آمده‌اند
    trends = []
    for topic, info in count.items():
        if len(info["sources"]) >= 2:
            trends.append({
                "topic": topic,
                "source_count": len(info["sources"]),
                "sources": list(info["sources"]),
                "links": info["links"][:3]  # فقط 3 لینک اول
            })
    
    # مرتب‌سازی بر اساس تعداد منابع
    trends.sort(key=lambda x: x["source_count"], reverse=True)
    return trends

# ============ COLLECTED NEWS ============
def save_collected_news(news_list):
    """ذخیره اخبار جمع‌آوری‌شده روزانه"""
    today = datetime.utcnow().date().isoformat()
    
    # بارگذاری داده‌های قبلی
    all_news = _load("collected_news", {})
    
    # اضافه کردن اخبار امروز
    if today not in all_news:
        all_news[today] = []
    
    # اضافه کردن اخبار جدید (بدون تکرار)
    existing_links = {news.get("link") for news in all_news[today]}
    
    for news in news_list:
        if news.get("link") not in existing_links:
            all_news[today].append(news)
            existing_links.add(news.get("link"))
    
    # حذف اخبار قدیمی‌تر از 7 روز
    cutoff_date = (datetime.utcnow().date() - datetime.timedelta(days=7)).isoformat()
    all_news = {date: news for date, news in all_news.items() if date >= cutoff_date}
    
    _save("collected_news", all_news)

def get_collected_news(limit=None, date=None):
    """خواندن اخبار جمع‌آوری‌شده"""
    all_news = _load("collected_news", {})
    
    if date is None:
        date = datetime.utcnow().date().isoformat()
    
    news = all_news.get(date, [])
    
    if limit:
        return news[:limit]
    return news

def get_all_collected_news(days=7):
    """دریافت تمام اخبار چند روز اخیر"""
    all_news = _load("collected_news", {})
    
    result = []
    for date in sorted(all_news.keys(), reverse=True)[:days]:
        result.extend(all_news[date])
    
    return result
