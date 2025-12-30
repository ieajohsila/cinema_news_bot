"""
ماژول تحلیل و ارسال ترندهای خبری سینما
"""

import json
import logging
from collections import Counter
from datetime import datetime
import os

logger = logging.getLogger(__name__)

# 🔧 FIX: مسیرهای صحیح
DAILY_NEWS_DIR = "data/daily_news"
TOPICS_FILE = "data/topics.json"

# ساخت پوشه‌ها
os.makedirs(DAILY_NEWS_DIR, exist_ok=True)
os.makedirs(os.path.dirname(TOPICS_FILE), exist_ok=True)


def save_daily_news(news_item):
    """
    🔧 FIX: ذخیره یک خبر در فایل روزانه
    """
    today = datetime.now().strftime("%Y-%m-%d")
    today_file = os.path.join(DAILY_NEWS_DIR, f"{today}.json")
    
    try:
        # خواندن فایل فعلی
        if os.path.exists(today_file):
            with open(today_file, "r", encoding="utf-8") as f:
                news_list = json.load(f)
        else:
            news_list = []
        
        # اضافه کردن خبر جدید
        news_list.append({
            "title": news_item.get("title", ""),
            "url": news_item.get("link", news_item.get("url", "")),
            "source": news_item.get("source", "unknown"),
            "summary": news_item.get("summary", "")[:200],
            "timestamp": datetime.now().isoformat()
        })
        
        # ذخیره
        with open(today_file, "w", encoding="utf-8") as f:
            json.dump(news_list, f, ensure_ascii=False, indent=2)
        
        logger.debug(f"✅ خبر در فایل روزانه ذخیره شد: {today_file}")
        
    except Exception as e:
        logger.error(f"❌ خطا در ذخیره خبر روزانه: {e}")


def load_topics():
    if os.path.exists(TOPICS_FILE):
        try:
            with open(TOPICS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading topics: {e}")
    return {}


def save_topics(topics):
    try:
        with open(TOPICS_FILE, "w", encoding="utf-8") as f:
            json.dump(topics, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving topics: {e}")


def save_topic(title, url, source):
    """ذخیره موضوع برای تحلیل ترند"""
    topics = load_topics()
    today = datetime.now().strftime("%Y-%m-%d")
    if today not in topics:
        topics[today] = []
    topics[today].append({
        "title": title,
        "sources": [source],
        "source_count": 1,
        "news_count": 1,
        "keywords": [],
        "urls": [url],
        "timestamp": datetime.now().isoformat()
    })
    save_topics(topics)


def extract_keywords(title, min_word_length=4):
    import re
    title_clean = re.sub(r'[^\w\s]', ' ', title.lower())
    stop_words = {'the', 'and', 'for', 'with', 'from', 'this', 'that', 'will',
                  'have', 'been', 'are', 'was', 'were', 'what', 'when', 'where',
                  'who', 'why', 'how', 'about', 'after', 'before', 'into', 'through',
                  'movie', 'film', 'new', 'first', 'more', 'gets', 'release', 'announced'}
    return [w for w in title_clean.split() if len(w) >= min_word_length and w not in stop_words]


def calculate_similarity(title1, title2):
    kws1 = set(extract_keywords(title1))
    kws2 = set(extract_keywords(title2))
    if not kws1 or not kws2:
        return 0.0
    return len(kws1 & kws2) / len(kws1 | kws2)


def group_similar_news(news_list, threshold=0.4):
    """گروه‌بندی اخبار مشابه"""
    groups = []
    used = set()
    for i, n1 in enumerate(news_list):
        if i in used: 
            continue
        group = [n1]
        used.add(i)
        for j, n2 in enumerate(news_list[i+1:], start=i+1):
            if j in used: 
                continue
            if calculate_similarity(n1['title'], n2['title']) >= threshold:
                group.append(n2)
                used.add(j)
        groups.append(group)
    return groups


def find_daily_trends(min_sources=2):
    """
    🔧 FIX: پیدا کردن ترندهای روزانه از فایل ذخیره شده
    """
    today = datetime.now().strftime("%Y-%m-%d")
    today_file = os.path.join(DAILY_NEWS_DIR, f"{today}.json")
    
    logger.info(f"🔍 جستجوی ترندها در: {today_file}")
    
    if not os.path.exists(today_file):
        logger.warning(f"⚠️ فایل اخبار امروز وجود ندارد: {today_file}")
        return []
    
    try:
        with open(today_file, "r", encoding="utf-8") as f:
            news_list = json.load(f)
        
        logger.info(f"✅ {len(news_list)} خبر از فایل روزانه خوانده شد")
        
        if len(news_list) < min_sources:
            logger.info(f"📊 تعداد اخبار ({len(news_list)}) کمتر از حد minimum ({min_sources}) است")
            return []
        
        # گروه‌بندی اخبار مشابه
        groups = group_similar_news(news_list)
        logger.info(f"📦 {len(groups)} گروه خبری شناسایی شد")
        
        trends = []
        for group in groups:
            if len(group) >= min_sources:
                sources = list(set([n['source'] for n in group]))
                best_title = max(group, key=lambda x: len(x['title']))['title']
                
                all_keywords = []
                for n in group:
                    all_keywords.extend(extract_keywords(n['title']))
                top_keywords = [kw for kw, _ in Counter(all_keywords).most_common(3)]
                
                trends.append({
                    "title": best_title,
                    "sources": sources,
                    "source_count": len(sources),
                    "news_count": len(group),
                    "keywords": top_keywords,
                    "urls": [n['url'] for n in group[:5]],
                    "timestamp": datetime.now().isoformat()
                })
        
        trends.sort(key=lambda x: x['source_count'], reverse=True)
        logger.info(f"🔥 {len(trends)} ترند با حداقل {min_sources} منبع پیدا شد")
        
        return trends
        
    except Exception as e:
        logger.error(f"❌ خطا در خواندن ترندها: {e}")
        return []


def format_trends_message(trends, max_trends=10):
    if not trends:
        return "🔍 هیچ ترند خبری امروز شناسایی نشد."
    
    trends = trends[:max_trends]
    today_date = datetime.now().strftime("%Y/%m/%d")
    parts = ["📊 *ترندهای خبری سینما*", f"📅 {today_date}", "", "🔥 *داغ‌ترین اخبار امروز:*", ""]
    
    for idx, t in enumerate(trends, 1):
        emoji = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else f"{idx}️⃣"
        txt = [
            f"{emoji} *{t['title']}*",
            f"   📰 منابع: {', '.join(t['sources'][:3])}"
        ]
        if len(t['sources']) > 3:
            txt.append(f"   ➕ و {len(t['sources'])-3} منبع دیگر")
        txt.append(f"   🔢 تعداد اخبار: {t['news_count']}")
        if t['urls']:
            txt.append(f"   🔗 [مشاهده خبر]({t['urls'][0]})")
        txt.append("")
        parts.extend(txt)
    
    parts.extend(["━━━━━━━━━━━━━━━━━", "🎬 *ربات خبری سینما*", f"⏰ آخرین بروزرسانی: {datetime.now().strftime('%H:%M')}"])
    return "\n".join(parts)
