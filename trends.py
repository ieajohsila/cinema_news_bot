"""
ماژول تحلیل و ارسال ترندهای خبری سینما
با پشتیبانی از اخبار ذخیره‌شده روزانه
"""

import json
import logging
from collections import Counter
from datetime import datetime
from typing import Dict, List
import os

from news_fetcher import get_collected_news

logger = logging.getLogger(__name__)

# مسیر فایل ذخیره topics
TOPICS_FILE = "data/topics.json"
os.makedirs(os.path.dirname(TOPICS_FILE), exist_ok=True)


def load_topics() -> Dict:
    """بارگذاری topics ذخیره شده"""
    if os.path.exists(TOPICS_FILE):
        try:
            with open(TOPICS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading topics: {e}")
    return {}


def save_topics(topics: Dict):
    """ذخیره topics"""
    try:
        with open(TOPICS_FILE, 'w', encoding='utf-8') as f:
            json.dump(topics, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving topics: {e}")


def extract_keywords(title: str, min_word_length: int = 4) -> List[str]:
    """استخراج کلمات کلیدی از عنوان خبر"""
    import re
    title_clean = re.sub(r'[^\w\s]', ' ', title.lower())
    stop_words = {
        'the', 'and', 'for', 'with', 'from', 'this', 'that', 'will', 
        'have', 'been', 'are', 'was', 'were', 'what', 'when', 'where',
        'who', 'why', 'how', 'about', 'after', 'before', 'into', 'through',
        'movie', 'film', 'new', 'first', 'more', 'gets', 'release', 'announced'
    }
    words = [w for w in title_clean.split() if len(w) >= min_word_length and w not in stop_words]
    return words


def calculate_similarity(title1: str, title2: str) -> float:
    """محاسبه شباهت بین دو عنوان"""
    keywords1 = set(extract_keywords(title1))
    keywords2 = set(extract_keywords(title2))
    if not keywords1 or not keywords2:
        return 0.0
    intersection = keywords1.intersection(keywords2)
    union = keywords1.union(keywords2)
    return len(intersection) / len(union) if union else 0.0


def group_similar_news(news_list: List[Dict], similarity_threshold: float = 0.4) -> List[List[Dict]]:
    """گروه‌بندی اخبار مشابه"""
    groups = []
    used = set()
    for i, news1 in enumerate(news_list):
        if i in used:
            continue
        group = [news1]
        used.add(i)
        for j, news2 in enumerate(news_list[i+1:], start=i+1):
            if j in used:
                continue
            if calculate_similarity(news1['title'], news2['title']) >= similarity_threshold:
                group.append(news2)
                used.add(j)
        groups.append(group)
    return groups


def find_daily_trends(min_sources: int = 2) -> List[Dict]:
    """پیدا کردن ترندهای روزانه از اخبار ذخیره‌شده روزانه"""
    today_news = get_collected_news()
    if not today_news:
        logger.info("No news found for today")
        return []
    groups = group_similar_news(today_news)
    trends = []
    for group in groups:
        if len(group) >= min_sources:
            sources = list(set([news.get('source', 'Unknown') for news in group]))
            best_title = max(group, key=lambda x: len(x.get('title', '')))['title']
            all_keywords = []
            for news in group:
                all_keywords.extend(extract_keywords(news['title']))
            keyword_counts = Counter(all_keywords)
            top_keywords = [kw for kw, _ in keyword_counts.most_common(3)]
            trend = {
                'title': best_title,
                'sources': sources,
                'source_count': len(sources),
                'news_count': len(group),
                'keywords': top_keywords,
                'urls': [news.get('url', '') for news in group[:5]],
                'timestamp': datetime.now().isoformat()
            }
            trends.append(trend)
    trends.sort(key=lambda x: x['source_count'], reverse=True)
    logger.info(f"Found {len(trends)} trends from {len(today_news)} news items")
    return trends


def format_trends_message(trends: List[Dict], max_trends: int = 10) -> str:
    """فرمت کردن پیام ترندها به صورت لیست زیبا"""
    if not trends:
        return "🔍 هیچ ترند خبری امروز شناسایی نشد."
    trends = trends[:max_trends]
    today_date = datetime.now().strftime("%Y/%m/%d")
    message_parts = [
        "📊 *ترندهای خبری سینما*",
        f"📅 {today_date}",
        "",
        "🔥 *داغ‌ترین اخبار امروز:*",
        ""
    ]
    for idx, trend in enumerate(trends, 1):
        emoji = ["🥇","🥈","🥉"][idx-1] if idx <=3 else f"{idx}️⃣"
        trend_text = [
            f"{emoji} *{trend['title']}*",
            f"   📰 منابع: {', '.join(trend['sources'][:3])}",
        ]
        if len(trend['sources']) > 3:
            trend_text.append(f"   ➕ و {len(trend['sources']) - 3} منبع دیگر")
        trend_text.append(f"   🔢 تعداد اخبار: {trend['news_count']}")
        if trend['urls'] and trend['urls'][0]:
            trend_text.append(f"   🔗 [مشاهده خبر]({trend['urls'][0]})")
        trend_text.append("")
        message_parts.extend(trend_text)
    message_parts.extend([
        "━━━━━━━━━━━━━━━━━",
        "🎬 *ربات خبری سینما*",
        f"⏰ آخرین بروزرسانی: {datetime.now().strftime('%H:%M')}"
    ])
    return "\n".join(message_parts)


def save_topic(title, link, source, date=None):
    """ذخیره یک خبر برای ترند روزانه"""
    topics = load_topics()
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    if date not in topics:
        topics[date] = []
    topic_data = {
        'title': title,
        'sources': [source],
        'source_count': 1,
        'news_count': 1,
        'keywords': extract_keywords(title),
        'urls': [link],
        'timestamp': datetime.now().isoformat()
    }
    topics[date].append(topic_data)
    save_topics(topics)
    logger.info(f"Saved topic: {title}")


# تست
if __name__ == "__main__":
    trends = find_daily_trends()
    message = format_trends_message(trends)
    print(message)
