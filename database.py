import json
import os
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Logger
logger = logging.getLogger(__name__)

# ================= BASE PATH =================
BASE = Path("data")
BASE.mkdir(exist_ok=True)

# ================= FILES =================
FILES = {
    "settings": BASE / "settings.json",
    "sources": BASE / "sources.json",
    "sent": BASE / "sent.json",
    "topics": BASE / "topics.json",
    "news": BASE / "collected_news.json",
}

# ================= HELPERS =================
def _ensure_file(path: Path, default):
    if not path.exists():
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False, indent=2)

def _load_file(path: Path, default):
    _ensure_file(path, default)
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def _save_file(path: Path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ================= SETTINGS =================
def get_setting(key, default=None):
    """
    🔧 FIX: اول از ENV بخوان، بعد از فایل
    """
    # 1. چک کردن Environment Variable
    env_value = os.getenv(key)
    if env_value is not None:
        return env_value
    
    # 2. چک کردن فایل تنظیمات
    data = _load_file(FILES["settings"], {})
    return data.get(key, default)

def set_setting(key, value):
    data = _load_file(FILES["settings"], {})
    data[key] = value
    _save_file(FILES["settings"], data)

# ================= SOURCES =================
def get_sources():
    return _load_file(FILES["sources"], {"rss": [], "scrape": []})

def get_rss_sources():
    return get_sources().get("rss", [])

def get_scrape_sources():
    return get_sources().get("scrape", [])

def add_rss_source(url):
    data = get_sources()
    if url not in data["rss"]:
        data["rss"].append(url)
        _save_file(FILES["sources"], data)

def add_scrape_source(url):
    data = get_sources()
    if url not in data["scrape"]:
        data["scrape"].append(url)
        _save_file(FILES["sources"], data)

def remove_rss_source(url):
    data = get_sources()
    if url in data["rss"]:
        data["rss"].remove(url)
        _save_file(FILES["sources"], data)

def remove_scrape_source(url):
    data = get_sources()
    if url in data["scrape"]:
        data["scrape"].remove(url)
        _save_file(FILES["sources"], data)

# ================= SENT (تکراری نبودن اخبار) =================
def is_sent(uid):
    """بررسی اینکه خبر قبلاً ارسال شده یا نه"""
    try:
        data = _load_file(FILES["sent"], [])
        # 🔧 FIX: تبدیل به string برای مقایسه
        return str(uid) in [str(x) for x in data]
    except Exception as e:
        logger.error(f"خطا در is_sent: {e}")
        return False

def mark_sent(uid):
    """علامت‌گذاری خبر به عنوان ارسال شده"""
    try:
        data = _load_file(FILES["sent"], [])
        uid_str = str(uid)
        
        # 🔧 FIX: چک کردن تکراری نبودن
        if uid_str not in [str(x) for x in data]:
            data.append(uid_str)
            
            # 🔧 FIX: نگه داشتن فقط 2000 آیتم آخر
            if len(data) > 2000:
                data = data[-2000:]
            
            _save_file(FILES["sent"], data)
            return True
        return False
    except Exception as e:
        logger.error(f"خطا در mark_sent: {e}")
        return False

# ================= COLLECTED NEWS =================
def save_collected_news(news_list):
    _save_file(FILES["news"], news_list)

def get_collected_news(limit=None):
    news = _load_file(FILES["news"], [])
    return news[:limit] if limit else news

# ================= TOPICS / TRENDS =================
def save_topic(topic, url, source):
    """ذخیره یک تاپیک برای تحلیل ترند"""
    data = _load_file(FILES["topics"], [])
    today = datetime.utcnow().date().isoformat()
    data.append({
        "topic": topic,
        "url": url,
        "source": source,
        "date": today
    })
    # نگه داشتن فقط 30 روز اخیر
    cutoff = (datetime.utcnow().date() - timedelta(days=30)).isoformat()
    data = [item for item in data if item.get("date", "") >= cutoff]
    _save_file(FILES["topics"], data)

def daily_trends(min_sources=3):
    """پیدا کردن ترندهای روزانه"""
    data = _load_file(FILES["topics"], [])
    today = datetime.utcnow().date().isoformat()
    count = {}

    for item in data:
        if item.get("date") == today:
            topic = item.get("topic", "")
            source = item.get("source", "")
            if topic:
                if topic not in count:
                    count[topic] = set()
                count[topic].add(source)

    # فیلتر ترندها با حداقل تعداد منبع
    trends = [topic for topic, sources in count.items() if len(sources) >= min_sources]
    return trendsimport json
import os
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Logger
logger = logging.getLogger(__name__)

# ================= BASE PATH =================
BASE = Path("data")
BASE.mkdir(exist_ok=True)

# ================= FILES =================
FILES = {
    "settings": BASE / "settings.json",
    "sources": BASE / "sources.json",
    "sent": BASE / "sent.json",
    "topics": BASE / "topics.json",
    "news": BASE / "collected_news.json",
}

# ================= HELPERS =================
def _ensure_file(path: Path, default):
    if not path.exists():
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False, indent=2)

def _load_file(path: Path, default):
    _ensure_file(path, default)
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def _save_file(path: Path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ================= SETTINGS =================
def get_setting(key, default=None):
    """
    🔧 FIX: اول از ENV بخوان، بعد از فایل
    """
    # 1. چک کردن Environment Variable
    env_value = os.getenv(key)
    if env_value is not None:
        return env_value
    
    # 2. چک کردن فایل تنظیمات
    data = _load_file(FILES["settings"], {})
    return data.get(key, default)

def set_setting(key, value):
    data = _load_file(FILES["settings"], {})
    data[key] = value
    _save_file(FILES["settings"], data)

# ================= SOURCES =================
def get_sources():
    return _load_file(FILES["sources"], {"rss": [], "scrape": []})

def get_rss_sources():
    return get_sources().get("rss", [])

def get_scrape_sources():
    return get_sources().get("scrape", [])

def add_rss_source(url):
    data = get_sources()
    if url not in data["rss"]:
        data["rss"].append(url)
        _save_file(FILES["sources"], data)

def add_scrape_source(url):
    data = get_sources()
    if url not in data["scrape"]:
        data["scrape"].append(url)
        _save_file(FILES["sources"], data)

def remove_rss_source(url):
    data = get_sources()
    if url in data["rss"]:
        data["rss"].remove(url)
        _save_file(FILES["sources"], data)

def remove_scrape_source(url):
    data = get_sources()
    if url in data["scrape"]:
        data["scrape"].remove(url)
        _save_file(FILES["sources"], data)

# ================= SENT (تکراری نبودن اخبار) =================
def is_sent(uid):
    """بررسی اینکه خبر قبلاً ارسال شده یا نه"""
    try:
        data = _load_file(FILES["sent"], [])
        # 🔧 FIX: تبدیل به string برای مقایسه
        return str(uid) in [str(x) for x in data]
    except Exception as e:
        logger.error(f"خطا در is_sent: {e}")
        return False

def mark_sent(uid):
    """علامت‌گذاری خبر به عنوان ارسال شده"""
    try:
        data = _load_file(FILES["sent"], [])
        uid_str = str(uid)
        
        # 🔧 FIX: چک کردن تکراری نبودن
        if uid_str not in [str(x) for x in data]:
            data.append(uid_str)
            
            # 🔧 FIX: نگه داشتن فقط 2000 آیتم آخر
            if len(data) > 2000:
                data = data[-2000:]
            
            _save_file(FILES["sent"], data)
            return True
        return False
    except Exception as e:
        logger.error(f"خطا در mark_sent: {e}")
        return False

# ================= COLLECTED NEWS =================
def save_collected_news(news_list):
    _save_file(FILES["news"], news_list)

def get_collected_news(limit=None):
    news = _load_file(FILES["news"], [])
    return news[:limit] if limit else news

# ================= TOPICS / TRENDS =================
def save_topic(topic, url, source):
    """ذخیره یک تاپیک برای تحلیل ترند"""
    data = _load_file(FILES["topics"], [])
    today = datetime.utcnow().date().isoformat()
    data.append({
        "topic": topic,
        "url": url,
        "source": source,
        "date": today
    })
    # نگه داشتن فقط 30 روز اخیر
    cutoff = (datetime.utcnow().date() - timedelta(days=30)).isoformat()
    data = [item for item in data if item.get("date", "") >= cutoff]
    _save_file(FILES["topics"], data)

def daily_trends(min_sources=3):
    """پیدا کردن ترندهای روزانه"""
    data = _load_file(FILES["topics"], [])
    today = datetime.utcnow().date().isoformat()
    count = {}

    for item in data:
        if item.get("date") == today:
            topic = item.get("topic", "")
            source = item.get("source", "")
            if topic:
                if topic not in count:
                    count[topic] = set()
                count[topic].add(source)

    # فیلتر ترندها با حداقل تعداد منبع
    trends = [topic for topic, sources in count.items() if len(sources) >= min_sources]
    return trends
