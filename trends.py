# trends.py
import json
import os
import re

TRENDS_FILE = "trends.json"

def _load_trends():
    if not os.path.exists(TRENDS_FILE):
        return []
    with open(TRENDS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def _save_trends(trends):
    with open(TRENDS_FILE, "w", encoding="utf-8") as f:
        json.dump(trends, f, ensure_ascii=False, indent=4)

def normalize(title):
    return " ".join(re.sub(r"[^a-z0-9 ]", "", title.lower()).split()[:6])

def save_topic(title, source, date):
    """ذخیره ترند با نرمال‌سازی عنوان"""
    trends = _load_trends()
    normalized_title = normalize(title)
    trends.append({
        "topic": normalized_title,
        "source": source,
        "date": date
    })
    _save_trends(trends)

def daily_trends(date):
    """برگرداندن ترندهایی که حداقل از دو منبع آمده باشند"""
    trends = _load_trends()
    counter = {}
    for item in trends:
        if item["date"] != date:
            continue
        key = item["topic"]
        counter.setdefault(key, set()).add(item["source"])

    # فقط موضوعاتی که از حداقل 2 منبع آمده باشند
    result = [(topic, len(sources)) for topic, sources in counter.items() if len(sources) >= 3]
    return result

