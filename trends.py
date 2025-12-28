"""
ماژول تحلیل و ارسال ترندهای خبری سینما
"""
import json
import logging
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os

logger = logging.getLogger(__name__)

# مسیر فایل ذخیره topics
TOPICS_FILE = "data/topics.json"


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
    os.makedirs(os.path.dirname(TOPICS_FILE), exist_ok=True)
    try:
        with open(TOPICS_FILE, 'w', encoding='utf-8') as f:
            json.dump(topics, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving topics: {e}")


# Backward compatibility: تابع قدیمی save_topic
def save_topic(topic_name: str, sources: List[str]):
    """
    تابع قدیمی برای سازگاری با نسخه‌های قبلی
    ذخیره یک topic با لیست منابع
    """
    topics = load_topics()
    today_key = datetime.now().strftime("%Y-%m-%d")
    
    if today_key not in topics:
        topics[today_key] = []
    
    # ساخت فرمت جدید از داده‌های قدیمی
    topic_data = {
        'title': topic_name,
        'sources': sources,
        'source_count': len(sources),
        'news_count': len(sources),
        'keywords': [],
        'urls': [],
        'timestamp': datetime.now().isoformat()
    }
    
    topics[today_key].append(topic_data)
    save_topics(topics)
    logger.info(f"Saved topic (legacy): {topic_name} with {len(sources)} sources")


def extract_keywords(title: str, min_word_length: int = 4) -> List[str]:
    """
    استخراج کلمات کلیدی از عنوان خبر
    
    Args:
        title: عنوان خبر
        min_word_length: حداقل طول کلمه برای در نظر گرفتن
    
    Returns:
        لیست کلمات کلیدی
    """
    # حذف کاراکترهای خاص
    import re
    title_clean = re.sub(r'[^\w\s]', ' ', title.lower())
    
    # کلمات رایج که نباید به عنوان keyword در نظر گرفته بشن
    stop_words = {
        'the', 'and', 'for', 'with', 'from', 'this', 'that', 'will', 
        'have', 'been', 'are', 'was', 'were', 'what', 'when', 'where',
        'who', 'why', 'how', 'about', 'after', 'before', 'into', 'through',
        'movie', 'film', 'new', 'first', 'more', 'gets', 'release', 'announced'
    }
    
    # استخراج کلمات
    words = [
        word for word in title_clean.split() 
        if len(word) >= min_word_length and word not in stop_words
    ]
    
    return words


def calculate_similarity(title1: str, title2: str) -> float:
    """
    محاسبه شباهت بین دو عنوان
    
    Returns:
        عدد بین 0 تا 1 که نشان‌دهنده میزان شباهت است
    """
    keywords1 = set(extract_keywords(title1))
    keywords2 = set(extract_keywords(title2))
    
    if not keywords1 or not keywords2:
        return 0.0
    
    # Jaccard similarity
    intersection = keywords1.intersection(keywords2)
    union = keywords1.union(keywords2)
    
    return len(intersection) / len(union) if union else 0.0


def group_similar_news(news_list: List[Dict], similarity_threshold: float = 0.4) -> List[List[Dict]]:
    """
    گروه‌بندی اخبار مشابه
    
    Args:
        news_list: لیست اخبار
        similarity_threshold: حد آستانه شباهت (0 تا 1)
    
    Returns:
        لیستی از گروه‌های خبری مشابه
    """
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
            
            similarity = calculate_similarity(news1['title'], news2['title'])
            
            if similarity >= similarity_threshold:
                group.append(news2)
                used.add(j)
        
        groups.append(group)
    
    return groups


def find_daily_trends(news_list: List[Dict], min_sources: int = 3) -> List[Dict]:
    """
    پیدا کردن ترندهای روزانه
    
    Args:
        news_list: لیست کل اخبار روز
        min_sources: حداقل تعداد منبع برای تبدیل شدن به ترند
    
    Returns:
        لیست ترندها با اطلاعات کامل
    """
    # فیلتر اخبار امروز
    today = datetime.now().date()
    today_news = [
        news for news in news_list 
        if datetime.fromisoformat(news.get('published', datetime.now().isoformat())).date() == today
    ]
    
    if not today_news:
        logger.info("No news found for today")
        return []
    
    # گروه‌بندی اخبار مشابه
    groups = group_similar_news(today_news)
    
    # پیدا کردن ترندها (گروه‌هایی با حداقل min_sources منبع)
    trends = []
    
    for group in groups:
        if len(group) >= min_sources:
            # استخراج منابع یکتا
            sources = list(set([news.get('source', 'Unknown') for news in group]))
            
            # انتخاب بهترین عنوان (طولانی‌ترین یا جامع‌ترین)
            best_title = max(group, key=lambda x: len(x.get('title', '')))['title']
            
            # شمارش کلمات کلیدی تکراری
            all_keywords = []
            for news in group:
                all_keywords.extend(extract_keywords(news['title']))
            
            keyword_counts = Counter(all_keywords)
            top_keywords = [kw for kw, count in keyword_counts.most_common(3)]
            
            trend = {
                'title': best_title,
                'sources': sources,
                'source_count': len(sources),
                'news_count': len(group),
                'keywords': top_keywords,
                'urls': [news.get('url', '') for news in group[:5]],  # حداکثر 5 لینک
                'timestamp': datetime.now().isoformat()
            }
            
            trends.append(trend)
    
    # مرتب‌سازی بر اساس تعداد منابع (از بیشترین به کمترین)
    trends.sort(key=lambda x: x['source_count'], reverse=True)
    
    logger.info(f"Found {len(trends)} trends from {len(today_news)} news items")
    
    return trends


def format_trends_message(trends: List[Dict], max_trends: int = 10) -> str:
    """
    فرمت کردن پیام ترندها به صورت لیست زیبا
    
    Args:
        trends: لیست ترندها
        max_trends: حداکثر تعداد ترند برای نمایش
    
    Returns:
        پیام فرمت شده
    """
    if not trends:
        return "🔍 هیچ ترند خبری امروز شناسایی نشد."
    
    # محدود کردن تعداد ترندها
    trends = trends[:max_trends]
    
    # تاریخ امروز
    today_date = datetime.now().strftime("%Y/%m/%d")
    
    # ساخت پیام
    message_parts = [
        "📊 *ترندهای خبری سینما*",
        f"📅 {today_date}",
        "",
        "🔥 *داغ‌ترین اخبار امروز:*",
        ""
    ]
    
    # اضافه کردن هر ترند
    for idx, trend in enumerate(trends, 1):
        # ایموجی بر اساس رتبه
        if idx == 1:
            emoji = "🥇"
        elif idx == 2:
            emoji = "🥈"
        elif idx == 3:
            emoji = "🥉"
        else:
            emoji = f"{idx}️⃣"
        
        # فرمت ترند
        trend_text = [
            f"{emoji} *{trend['title']}*",
            f"   📰 منابع: {', '.join(trend['sources'][:3])}",  # حداکثر 3 منبع
        ]
        
        # اگر بیش از 3 منبع داره
        if len(trend['sources']) > 3:
            trend_text.append(f"   ➕ و {len(trend['sources']) - 3} منبع دیگر")
        
        # اضافه کردن تعداد اخبار
        trend_text.append(f"   🔢 تعداد اخبار: {trend['news_count']}")
        
        # اضافه کردن لینک اولین خبر
        if trend['urls'] and trend['urls'][0]:
            trend_text.append(f"   🔗 [مشاهده خبر]({trend['urls'][0]})")
        
        trend_text.append("")  # خط خالی بین ترندها
        
        message_parts.extend(trend_text)
    
    # اضافه کردن footer
    message_parts.extend([
        "━━━━━━━━━━━━━━━━━",
        "🎬 *ربات خبری سینما*",
        f"⏰ آخرین بروزرسانی: {datetime.now().strftime('%H:%M')}"
    ])
    
    return "\n".join(message_parts)


# Backward compatibility: alias برای تابع قدیمی
def format_trend_message(trends: List[Dict], max_trends: int = 10) -> str:
    """
    تابع قدیمی برای سازگاری با نسخه‌های قبلی
    """
    return format_trends_message(trends, max_trends)


def send_daily_trends(bot, chat_id: int, news_list: List[Dict], min_sources: int = 3):
    """
    ارسال ترندهای روزانه به کانال
    
    Args:
        bot: نمونه ربات تلگرام
        chat_id: آیدی کانال/گروه مقصد
        news_list: لیست کل اخبار
        min_sources: حداقل تعداد منبع برای تبدیل شدن به ترند
    """
    try:
        # پیدا کردن ترندها
        trends = find_daily_trends(news_list, min_sources)
        
        if not trends:
            logger.info("No trends to send today")
            return
        
        # فرمت کردن پیام
        message = format_trends_message(trends)
        
        # ارسال پیام
        bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode='Markdown',
            disable_web_page_preview=False
        )
        
        logger.info(f"Successfully sent {len(trends)} trends to {chat_id}")
        
        # ذخیره ترندها
        topics = load_topics()
        today_key = datetime.now().strftime("%Y-%m-%d")
        topics[today_key] = trends
        save_topics(topics)
        
    except Exception as e:
        logger.error(f"Error sending daily trends: {e}")


# تست
if __name__ == "__main__":
    # نمونه اخبار برای تست
    test_news = [
        {
            'title': 'Christopher Nolan Wins Best Director at Oscars 2024',
            'source': 'Variety',
            'published': datetime.now().isoformat(),
            'url': 'https://example.com/1'
        },
        {
            'title': 'Nolan Takes Home Best Director Oscar for Oppenheimer',
            'source': 'Hollywood Reporter',
            'published': datetime.now().isoformat(),
            'url': 'https://example.com/2'
        },
        {
            'title': 'Christopher Nolan Wins Oscar for Directing Oppenheimer',
            'source': 'Deadline',
            'published': datetime.now().isoformat(),
            'url': 'https://example.com/3'
        },
        {
            'title': 'Barbie Movie Breaks Box Office Records',
            'source': 'BoxOfficeMojo',
            'published': datetime.now().isoformat(),
            'url': 'https://example.com/4'
        },
    ]
    
    trends = find_daily_trends(test_news, min_sources=2)
    message = format_trends_message(trends)
    print(message)
