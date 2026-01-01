"""
ماژول رتبه‌بندی و تحلیل اخبار
"""

import re
from collections import Counter
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


# کلمات کلیدی مهم در دنیای سینما
IMPORTANT_KEYWORDS = {
    # نام‌های بزرگ و برندها
    "oscar", "academy", "cannes", "berlin", "venice", "sundance", "golden globe",
    "spielberg", "nolan", "tarantino", "scorsese", "coppola", "kubrick",
    "marvel", "disney", "warner", "netflix", "apple tv", "hbo", "amazon",
    
    # ژانرها و موضوعات مهم
    "box office", "blockbuster", "premiere", "release", "trailer", "teaser",
    "award", "nomination", "winner", "festival", "competition",
    "director", "actor", "actress", "cast", "star",
    "breaking", "exclusive", "announced", "confirmed",
    
    # کلمات فارسی
    "اسکار", "جایزه", "فیلم", "کارگردان", "بازیگر",
    "فروش", "اکران", "تریلر", "جشنواره", "کن",
}

# کلمات منفی (اخبار کم‌اهمیت)
NEGATIVE_KEYWORDS = {
    "rumor", "speculation", "might", "could", "possibly", "allegedly",
    "unconfirmed", "gossip",
    "شایعه", "احتمال", "ممکن است",
}

# کلمات فوری (اهمیت بالا)
URGENT_KEYWORDS = {
    "breaking", "dies", "death", "dead", "passed away",
    "wins oscar", "oscar winner", "best picture",
    "record breaking", "historic", "unprecedented",
    "فوت", "درگذشت", "برنده اسکار",
}


def calculate_importance(article):
    """محاسبه اهمیت یک خبر (0 تا 3)"""
    score = 1.0  # امتیاز پایه
    
    title = article.get("title", "").lower()
    summary = article.get("summary", "").lower()
    text = title + " " + summary
    
    # چک کردن کلمات فوری (خیلی مهم)
    urgent_count = sum(1 for keyword in URGENT_KEYWORDS if keyword in text)
    if urgent_count > 0:
        score += 2
    
    # چک کردن کلمات کلیدی مهم
    important_count = sum(1 for keyword in IMPORTANT_KEYWORDS if keyword in text)
    score += min(important_count * 0.5, 1.5)  # حداکثر +1.5 امتیاز
    
    # کم کردن امتیاز برای کلمات منفی
    negative_count = sum(1 for keyword in NEGATIVE_KEYWORDS if keyword in text)
    score -= negative_count * 0.5
    
    # بررسی طول محتوا (محتوای طولانی‌تر معمولاً مهم‌تر است)
    if len(summary) > 250:
        score += 0.5
    elif len(summary) < 50:
        score -= 0.3
    
    # بررسی تازگی خبر
    published = article.get("published")
    if published:
        try:
            if isinstance(published, str):
                published = datetime.fromisoformat(published)
            
            age_hours = (datetime.now() - published).total_seconds() / 3600
            
            if age_hours < 6:  # خیلی تازه
                score += 0.8
            elif age_hours < 24:  # تازه
                score += 0.5
            elif age_hours > 120:  # خیلی قدیمی (5 روز)
                score -= 0.8
        except:
            pass
    
    # بررسی عنوان (عناوین کوتاه‌تر معمولاً بهتر هستند)
    if 30 < len(title) < 100:
        score += 0.2
    
    # محدود کردن به بازه 0-3
    score = max(0, min(3, round(score)))
    
    return int(score)


def rank_news(articles, min_importance=1):
    """رتبه‌بندی اخبار بر اساس اهمیت"""
    if not articles:
        logger.info("📭 هیچ خبری برای رتبه‌بندی وجود ندارد")
        return []
    
    logger.info(f"📊 شروع رتبه‌بندی {len(articles)} خبر...")
    
    ranked = []
    importance_counts = {0: 0, 1: 0, 2: 0, 3: 0}
    
    for article in articles:
        importance = calculate_importance(article)
        importance_counts[importance] += 1
        
        if importance >= min_importance:
            article["importance"] = importance
            ranked.append(article)
    
    # مرتب‌سازی بر اساس اهمیت (بالاترین اول)
    ranked.sort(key=lambda x: x["importance"], reverse=True)
    
    # لاگ آماری
    logger.info(f"📈 آمار اهمیت اخبار:")
    logger.info(f"   ⭐⭐⭐ سطح 3 (فوری): {importance_counts[3]} خبر")
    logger.info(f"   ⭐⭐ سطح 2 (مهم): {importance_counts[2]} خبر")
    logger.info(f"   ⭐ سطح 1 (معمولی): {importance_counts[1]} خبر")
    logger.info(f"   • سطح 0 (کم‌اهمیت): {importance_counts[0]} خبر")
    logger.info(f"✅ تعداد اخبار منتخب (حداقل سطح {min_importance}): {len(ranked)}")
    
    return ranked


def extract_keywords(text, min_length=4):
    """استخراج کلمات کلیدی از متن"""
    # حذف کاراکترهای خاص و تبدیل به حروف کوچک
    text = re.sub(r'[^\w\s]', ' ', text.lower())
    
    # تقسیم به کلمات
    words = text.split()
    
    # فیلتر کلمات (حداقل طول و حذف stop words ساده)
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
        'و', 'یا', 'در', 'به', 'از', 'که', 'این', 'آن', 'را'
    }
    
    keywords = [
        word for word in words 
        if len(word) >= min_length and word not in stop_words
    ]
    
    return keywords


def find_common_topics(articles):
    """پیدا کردن موضوعات مشترک بین اخبار"""
    all_keywords = []
    
    for article in articles:
        title = article.get("title", "")
        summary = article.get("summary", "")
        text = title + " " + summary
        
        keywords = extract_keywords(text)
        all_keywords.extend(keywords)
    
    # شمارش فراوانی
    keyword_counts = Counter(all_keywords)
    
    # برگرداندن 10 کلمه پرتکرار
    return keyword_counts.most_common(10)


def generate_daily_trend(articles):
    """تولید خلاصه ترند روزانه"""
    if not articles:
        return "امروز خبر جدیدی نبود."
    
    logger.info(f"📊 تحلیل ترند از {len(articles)} خبر...")
    
    # فقط اخبار امروز
    today = datetime.now().date()
    recent_articles = []
    
    for article in articles:
        pub_date = article.get("published")
        if pub_date:
            try:
                if isinstance(pub_date, str):
                    pub_date = datetime.fromisoformat(pub_date).date()
                elif isinstance(pub_date, datetime):
                    pub_date = pub_date.date()
                
                if (today - pub_date).days <= 1:  # امروز و دیروز
                    recent_articles.append(article)
            except:
                pass
    
    if not recent_articles:
        return "امروز خبر جدیدی نبود."
    
    # پیدا کردن موضوعات داغ
    topics = find_common_topics(recent_articles)
    
    if not topics:
        return f"امروز {len(recent_articles)} خبر منتشر شد."
    
    # ساخت خلاصه
    summary = f"📊 *ترند امروز سینما*\n\n"
    summary += f"🔥 *داغ‌ترین موضوعات:*\n"
    
    for i, (topic, count) in enumerate(topics[:5], 1):
        summary += f"{i}. {topic.title()} ({count} بار)\n"
    
    summary += f"\n📰 تعداد کل اخبار: {len(recent_articles)}"
    
    # اضافه کردن مهم‌ترین خبر
    important_news = [a for a in recent_articles if calculate_importance(a) >= 2]
    if important_news:
        summary += f"\n⭐ تعداد اخبار مهم: {len(important_news)}"
        
        # مهم‌ترین خبر
        top_news = max(important_news, key=lambda x: calculate_importance(x))
        summary += f"\n\n🌟 *برجسته‌ترین خبر:*\n{top_news['title'][:100]}"
    
    return summary


if __name__ == "__main__":
    # تست
    test_articles = [
        {
            "title": "Breaking: Director Christopher Nolan wins Oscar for Best Picture",
            "summary": "Historic achievement in cinema",
            "published": datetime.now().isoformat(),
        },
        {
            "title": "New Marvel movie trailer released",
            "summary": "Fans excited for upcoming blockbuster",
            "published": (datetime.now() - timedelta(hours=5)).isoformat(),
        }
    ]
    
    print("🧪 تست رتبه‌بندی...\n")
    ranked = rank_news(test_articles, min_importance=1)
    
    for news in ranked:
        print(f"\n⭐ اهمیت: {news['importance']}")
        print(f"📰 {news['title']}")
    
    print("\n\n📊 تست ترند...\n")
    trend = generate_daily_trend(test_articles)
    print(trend)
