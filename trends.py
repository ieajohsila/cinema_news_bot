"""
مدیریت و تحلیل ترندهای روزانه
"""

import json
import os
import re
from datetime import datetime
from collections import Counter
import jdatetime

TRENDS_FILE = "data/trends.json"


def _load_trends():
    """بارگذاری ترندها از فایل"""
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(TRENDS_FILE):
        return []
    with open(TRENDS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_trends(trends):
    """ذخیره ترندها"""
    os.makedirs("data", exist_ok=True)
    with open(TRENDS_FILE, "w", encoding="utf-8") as f:
        json.dump(trends, f, ensure_ascii=False, indent=2)


def normalize(title):
    """نرمال‌سازی عنوان برای مقایسه"""
    # حذف کاراکترهای خاص
    title = re.sub(r'[^\w\s]', ' ', title.lower())
    # حذف فضاهای اضافی
    title = ' '.join(title.split())
    # فقط 10 کلمه اول
    words = title.split()[:10]
    return ' '.join(words)


def save_topic(title, link, source, date):
    """ذخیره یک موضوع/خبر"""
    trends = _load_trends()
    
    normalized_title = normalize(title)
    
    trends.append({
        "title": title,
        "normalized_title": normalized_title,
        "link": link,
        "source": source,
        "date": date
    })
    
    _save_trends(trends)


def get_daily_trends(date, min_sources=2):
    """
    دریافت ترندهای یک روز خاص
    
    Args:
        date: تاریخ به فرمت ISO (YYYY-MM-DD)
        min_sources: حداقل تعداد منابع برای تبدیل به ترند
    
    Returns:
        لیست ترندها با تعداد منابع و لینک‌ها
    """
    trends = _load_trends()
    
    # فیلتر کردن ترندهای روز مورد نظر
    daily_items = [t for t in trends if t["date"] == date]
    
    if not daily_items:
        return []
    
    # گروه‌بندی بر اساس عنوان نرمال شده
    grouped = {}
    for item in daily_items:
        norm_title = item["normalized_title"]
        
        if norm_title not in grouped:
            grouped[norm_title] = {
                "title": item["title"],  # عنوان اصلی اولین خبر
                "sources": set(),
                "links": []
            }
        
        grouped[norm_title]["sources"].add(item["source"])
        grouped[norm_title]["links"].append({
            "link": item["link"],
            "source": item["source"]
        })
    
    # فیلتر کردن فقط موارد با حداقل منبع مورد نیاز
    result = []
    for norm_title, data in grouped.items():
        source_count = len(data["sources"])
        if source_count >= min_sources:
            result.append({
                "title": data["title"],
                "source_count": source_count,
                "links": data["links"][:3]  # فقط 3 لینک اول
            })
    
    # مرتب‌سازی بر اساس تعداد منابع (بیشترین اول)
    result.sort(key=lambda x: x["source_count"], reverse=True)
    
    return result


def format_trend_message(date, min_sources=2):
    """
    ساخت پیام فرمت شده ترندهای روز
    
    Args:
        date: تاریخ به فرمت ISO
        min_sources: حداقل منابع
    
    Returns:
        پیام فرمت شده با Markdown
    """
    trends = get_daily_trends(date, min_sources)
    
    if not trends:
        return None
    
    # تبدیل تاریخ به شمسی و میلادی
    try:
        dt = datetime.fromisoformat(date)
        jdt = jdatetime.datetime.fromgregorian(datetime=dt)
        
        persian_date = jdt.strftime('%Y/%m/%d')
        gregorian_date = dt.strftime('%Y-%m-%d')
        
        day_name_fa = jdt.strftime('%A')  # نام روز فارسی
    except:
        persian_date = date
        gregorian_date = date
        day_name_fa = ""
    
    # ساخت پیام
    msg = "📊 *ترندهای روز سینما*\n\n"
    msg += f"📅 {day_name_fa} {persian_date}\n"
    msg += f"📆 میلادی: {gregorian_date}\n\n"
    msg += f"🔥 *داغ‌ترین اخبار روز* (حداقل {min_sources} منبع):\n\n"
    
    for i, trend in enumerate(trends[:10], 1):  # فقط 10 ترند اول
        title = trend["title"][:100]  # محدود کردن طول عنوان
        count = trend["source_count"]
        first_link = trend["links"][0]["link"] if trend["links"] else "#"
        
        msg += f"{i}. [{title}]({first_link})\n"
        msg += f"   📰 {count} منبع\n\n"
    
    msg += f"_✅ مجموع {len(trends)} ترند یافت شد_"
    
    return msg


def clear_old_trends(days=7):
    """حذف ترندهای قدیمی‌تر از N روز"""
    trends = _load_trends()
    today = datetime.now().date()
    
    filtered = []
    for t in trends:
        try:
            trend_date = datetime.fromisoformat(t["date"]).date()
            age = (today - trend_date).days
            if age <= days:
                filtered.append(t)
        except:
            # اگر تاریخ معتبر نبود، نگه دار
            filtered.append(t)
    
    _save_trends(filtered)
    return len(trends) - len(filtered)


if __name__ == "__main__":
    # تست
    print("🧪 تست سیستم ترندها...\n")
    
    # تست ذخیره
    today = datetime.now().date().isoformat()
    save_topic("Breaking: New Marvel Movie Announced", "http://example.com/1", "source1", today)
    save_topic("Marvel announces new blockbuster film", "http://example.com/2", "source2", today)
    save_topic("Exciting Marvel News: New Film Coming", "http://example.com/3", "source3", today)
    
    # تست دریافت
    trends = get_daily_trends(today, min_sources=2)
    print(f"✅ {len(trends)} ترند یافت شد\n")
    
    # تست فرمت
    msg = format_trend_message(today, min_sources=2)
    if msg:
        print(msg)
    else:
        print("❌ ترندی یافت نشد")
