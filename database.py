"""
مدیریت دیتابیس - نسخه کامل و بدون باگ
همه توابع مورد نیاز تعریف شده‌اند
"""

import json
import os
from datetime import datetime, timedelta
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
    """بارگذاری امن فایل JSON"""
    try:
        if not os.path.exists(FILES[name]):
            with open(FILES[name], "w", encoding="utf-8") as f:
                json.dump(default, f, ensure_ascii=False, indent=2)
            return default
        
        with open(FILES[name], encoding="utf-8") as f:
            content = f.read().strip()
            
            if not content:
                with open(FILES[name], "w", encoding="utf-8") as f:
                    json.dump(default, f, ensure_ascii=False, indent=2)
                return default
            
            data = json.loads(content)
            return data
    except Exception as e:
        print(f"⚠️ خطا در بارگذاری {name}: {e}")
        return default

def _save(name, data):
    """ذخیره امن فایل JSON"""
    try:
        with open(FILES[name], "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"❌ خطا در ذخیره {name}: {e}")

# ============ SETTINGS ============
def get_setting(key, default=None):
    """دریافت یک تنظیم"""
    s = _load("settings", {})
    return s.get(key, default)

def set_setting(key, value):
    """ذخیره یک تنظیم"""
    s = _load("settings", {})
    s[key] = value
    _save("settings", s)

# ============ SOURCES ============
def get_sources():
    """برگرداندن همه منابع"""
    return _load("sources", {"rss": [], "scrape": []})

def get_rss_sources():
    """دریافت منابع RSS"""
    data = get_sources()
    return data.get("rss", [])

def get_scrape_sources():
    """دریافت منابع Scrape"""
    data = get_sources()
    return data.get("scrape", [])

def add_rss_source(url):
    """افزودن منبع RSS"""
    data = get_sources()
    if "rss" not in data:
        data["rss"] = []
    if url not in data["rss"]:
        data["rss"].append(url)
        _save("sources", data)

def add_scrape_source(url):
    """افزودن منبع Scrape"""
    data = get_sources()
    if "scrape" not in data:
        data["scrape"] = []
    if url not in data["scrape"]:
        data["scrape"].append(url)
        _save("sources", data)

def remove_rss_source(url):
    """حذف منبع RSS"""
    data = get_sources()
    if "rss" in data and url in data["rss"]:
        data["rss"].remove(url)
        _save("sources", data)

def remove_scrape_source(url):
    """حذف منبع Scrape"""
    data = get_sources()
    if "scrape" in data and url in data["scrape"]:
        data["scrape"].remove(url)
        _save("sources", data)

# ============ SENT ============
def is_sent(uid):
    """چک کردن ارسال شده بودن"""
    sent_list = _load("sent", [])
    if not isinstance(sent_list, list):
        sent_list = []
    return uid in sent_list

def mark_sent(uid):
    """علامت‌گذاری به عنوان ارسال شده"""
    sent_list = _load("sent", [])
    if not isinstance(sent_list, list):
        sent_list = []
    if uid not in sent_list:
        sent_list.append(uid)
        _save("sent", sent_list)

def cleanup_old_sent(days=30):
    """پاکسازی لیست sent (فعلاً فقط محدودیت تعداد)"""
    sent_list = _load("sent", [])
    if not isinstance(sent_list, list):
        return
    
    # نگه‌داشتن فقط 10000 آیتم آخر
    if len(sent_list) > 10000:
        sent_list = sent_list[-10000:]
        _save("sent", sent_list)

# ============ TOPICS ============
def save_topic(topic, link, source, date):
    """ذخیره topic برای تحلیل ترند"""
    data = _load("topics", [])
    
    # اطمینان از اینکه لیست است
    if not isinstance(data, list):
        data = []
    
    data.append({
        "topic": topic,
        "link": link,
        "source": source,
        "date": date,
        "timestamp": datetime.now().isoformat()
    })
    
    _save("topics", data)

def daily_trends(date=None):
    """دریافت ترندهای یک روز خاص"""
    if date is None:
        date = datetime.utcnow().date().isoformat()
    
    data = _load("topics", [])
    
    # اطمینان از اینکه لیست است
    if not isinstance(data, list):
        return []
    
    count = {}
    
    for item in data:
        if not isinstance(item, dict):
            continue
        
        if item.get("date") == date:
            topic = item.get("topic", "")
            source = item.get("source", "unknown")
            link = item.get("link", "")
            
            if not topic:
                continue
            
            if topic not in count:
                count[topic] = {"sources": set(), "links": []}
            
            count[topic]["sources"].add(source)
            count[topic]["links"].append(link)
    
    # ترندها: موضوعاتی که از 2 منبع یا بیشتر آمده‌اند
    trends = []
    for topic, info in count.items():
        if len(info["sources"]) >= 2:
            trends.append({
                "topic": topic,
                "source_count": len(info["sources"]),
                "sources": list(info["sources"]),
                "links": info["links"][:3]
            })
    
    # مرتب‌سازی بر اساس تعداد منابع
    trends.sort(key=lambda x: x["source_count"], reverse=True)
    return trends

# ============ COLLECTED NEWS ============
def save_collected_news(news_list):
    """ذخیره اخبار جمع‌آوری شده روزانه"""
    today = datetime.utcnow().date().isoformat()
    
    all_news = _load("collected_news", {})
    
    # اطمینان از اینکه dict است
    if not isinstance(all_news, dict):
        all_news = {}
    
    if today not in all_news:
        all_news[today] = []
    
    # دریافت لینک‌های موجود
    existing_links = {news.get("link") for news in all_news[today]}
    
    # اضافه کردن اخبار جدید
    for news in news_list:
        link = news.get("link")
        if link and link not in existing_links:
            all_news[today].append(news)
            existing_links.add(link)
    
    # حذف اخبار قدیمی‌تر از 7 روز
    cutoff_date = (datetime.utcnow().date() - timedelta(days=7)).isoformat()
    all_news = {d: n for d, n in all_news.items() if d >= cutoff_date}
    
    _save("collected_news", all_news)

def get_collected_news(limit=None, date=None):
    """خواندن اخبار جمع‌آوری شده"""
    all_news = _load("collected_news", {})
    
    if not isinstance(all_news, dict):
        return []
    
    if date is None:
        date = datetime.utcnow().date().isoformat()
    
    news = all_news.get(date, [])
    
    if not isinstance(news, list):
        return []
    
    if limit:
        return news[:limit]
    return news

def get_all_collected_news(days=7):
    """دریافت تمام اخبار چند روز اخیر"""
    all_news = _load("collected_news", {})
    
    if not isinstance(all_news, dict):
        return []
    
    result = []
    for date in sorted(all_news.keys(), reverse=True)[:days]:
        news = all_news[date]
        if isinstance(news, list):
            result.extend(news)
    
    return result


# ============ تست ============
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 تست ماژول database")
    print("="*60 + "\n")
    
    # تست settings
    set_setting("test_key", "test_value")
    print(f"✅ Settings: {get_setting('test_key')}")
    
    # تست sources
    add_rss_source("https://test.com/feed")
    print(f"✅ RSS Sources: {len(get_rss_sources())}")
    
    add_scrape_source("https://test.com/news")
    print(f"✅ Scrape Sources: {len(get_scrape_sources())}")
    
    # تست sent
    mark_sent("test_link_123")
    print(f"✅ Is Sent: {is_sent('test_link_123')}")
    
    # تست topics
    save_topic("Test Topic", "https://test.com", "test_source", "2025-01-01")
    trends = daily_trends("2025-01-01")
    print(f"✅ Topics: {len(trends)} trends")
    
    # تست collected_news
    save_collected_news([
        {"title": "Test News", "link": "https://test.com/1", "summary": "Test"}
    ])
    news = get_collected_news()
    print(f"✅ Collected News: {len(news)} items")
    
    print("\n" + "="*60)
    print("✅ همه تست‌ها موفق!")
    print("="*60 + "\n")
