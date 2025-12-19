"""
مدیریت وضعیت و آمار ربات
"""

from datetime import datetime, timedelta
import jdatetime
from database import get_setting, get_rss_sources, get_scrape_sources


def format_timedelta(td):
    """تبدیل timedelta به فرمت خوانای فارسی"""
    if not isinstance(td, timedelta):
        return "نامشخص"
    
    total_seconds = int(td.total_seconds())
    
    if total_seconds < 0:
        return "گذشته"
    
    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60
    
    parts = []
    if days > 0:
        parts.append(f"{days} روز")
    if hours > 0:
        parts.append(f"{hours} ساعت")
    if minutes > 0:
        parts.append(f"{minutes} دقیقه")
    
    if not parts:
        return "کمتر از یک دقیقه"
    
    return " و ".join(parts)


def format_datetime_persian(dt_str):
    """تبدیل datetime به فرمت فارسی"""
    if not dt_str:
        return "هرگز"
    
    try:
        dt = datetime.fromisoformat(dt_str)
        jdt = jdatetime.datetime.fromgregorian(datetime=dt)
        
        # فرمت: 1403/09/30 ساعت 14:25
        return jdt.strftime('%Y/%m/%d ساعت %H:%M')
    except:
        return dt_str


def format_datetime_dual(dt_str):
    """نمایش تاریخ به دو فرمت شمسی و میلادی"""
    if not dt_str:
        return "هرگز"
    
    try:
        dt = datetime.fromisoformat(dt_str)
        jdt = jdatetime.datetime.fromgregorian(datetime=dt)
        
        # فرمت شمسی
        persian = jdt.strftime('%Y/%m/%d')
        # فرمت میلادی
        gregorian = dt.strftime('%Y-%m-%d')
        
        return f"📅 {persian} (میلادی: {gregorian})"
    except:
        return dt_str


def get_status_message():
    """دریافت پیام کامل وضعیت ربات"""
    
    # دریافت تنظیمات
    target_chat = get_setting("TARGET_CHAT_ID", "تنظیم نشده")
    min_importance = get_setting("min_importance", "1")
    
    # زمان‌ها
    last_fetch = get_setting("last_news_fetch")
    last_send = get_setting("last_news_send")
    next_fetch = get_setting("next_news_fetch")
    next_trend = get_setting("next_trend_time")
    
    # محاسبه زمان باقی‌مانده تا جمع‌آوری بعدی
    if next_fetch:
        try:
            next_dt = datetime.fromisoformat(next_fetch)
            time_left = next_dt - datetime.now()
            next_fetch_str = format_timedelta(time_left) + " دیگر"
        except:
            next_fetch_str = format_datetime_persian(next_fetch)
    else:
        next_fetch_str = "نامشخص"
    
    # زمان ترند بعدی
    if next_trend:
        next_trend_str = format_datetime_persian(next_trend)
    else:
        next_trend_str = "نامشخص"
    
    # منابع
    rss_count = len(get_rss_sources())
    scrape_count = len(get_scrape_sources())
    
    # ساخت پیام
    msg = "📊 *وضعیت ربات خبری سینما*\n\n"
    
    msg += "⏰ *زمان‌بندی:*\n"
    msg += f"📰 جمع‌آوری بعدی: {next_fetch_str}\n"
    msg += f"📊 ترند بعدی: {next_trend_str}\n\n"
    
    msg += "✅ *آخرین فعالیت‌ها:*\n"
    msg += f"🔄 آخرین جمع‌آوری: {format_datetime_persian(last_fetch)}\n"
    msg += f"📤 آخرین ارسال: {format_datetime_persian(last_send)}\n\n"
    
    msg += "📰 *منابع فعال:*\n"
    msg += f"📡 RSS: {rss_count} منبع\n"
    msg += f"🕷️ Scraping: {scrape_count} منبع\n"
    msg += f"📊 مجموع: {rss_count + scrape_count} منبع\n\n"
    
    msg += "🎯 *تنظیمات:*\n"
    msg += f"📢 کانال مقصد: `{target_chat}`\n"
    msg += f"⭐ حداقل اهمیت: {min_importance}/3\n\n"
    
    msg += "_💡 برای بروزرسانی روی دکمه 🔄 کلیک کنید_"
    
    return msg


if __name__ == "__main__":
    # تست
    print(get_status_message())
