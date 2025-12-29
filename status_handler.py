"""
مدیریت وضعیت و آمار ربات
با پشتیبانی از Timezone تهران
"""

from datetime import datetime, timedelta
import jdatetime
import pytz
from database import get_setting, get_rss_sources, get_scrape_sources

# Timezone تهران
TEHRAN_TZ = pytz.timezone('Asia/Tehran')


def now_tehran():
    """دریافت زمان فعلی تهران"""
    return datetime.now(TEHRAN_TZ)


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


def parse_datetime_with_tz(dt_str):
    """تبدیل string به datetime با timezone"""
    if not dt_str:
        return None

    try:
        if isinstance(dt_str, datetime):
            dt = dt_str
        else:
            if dt_str.endswith('Z'):
                dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
            else:
                dt = datetime.fromisoformat(dt_str)

        if dt.tzinfo is None:
            dt = pytz.utc.localize(dt)

        return dt.astimezone(TEHRAN_TZ)

    except Exception:
        return None


def format_datetime_persian(dt_str):
    """تبدیل datetime به فرمت فارسی"""
    if not dt_str:
        return "هرگز"

    dt = parse_datetime_with_tz(dt_str)
    if not dt:
        return str(dt_str)

    try:
        jdt = jdatetime.datetime.fromgregorian(
            datetime=dt.replace(tzinfo=None)
        )
        return jdt.strftime('%Y/%m/%d ساعت %H:%M')
    except Exception:
        return dt.strftime('%Y-%m-%d %H:%M')


def format_datetime_dual(dt_str):
    """نمایش تاریخ به دو فرمت شمسی و میلادی"""
    if not dt_str:
        return "هرگز"

    dt = parse_datetime_with_tz(dt_str)
    if not dt:
        return str(dt_str)

    try:
        jdt = jdatetime.datetime.fromgregorian(
            datetime=dt.replace(tzinfo=None)
        )
        persian = jdt.strftime('%Y/%m/%d')
        gregorian = dt.strftime('%Y-%m-%d')
        return f"📅 {persian} (میلادی: {gregorian})"
    except Exception:
        return dt.strftime('%Y-%m-%d')


def get_status_message():
    """دریافت پیام کامل وضعیت ربات"""

    now = now_tehran()

    target_chat = get_setting("TARGET_CHAT_ID", "تنظیم نشده")
    min_importance = get_setting("min_importance", "1")
    fetch_interval = get_setting("news_fetch_interval_hours", "3")
    trend_hour = get_setting("trend_hour", "23")
    trend_minute = get_setting("trend_minute", "55")
    min_trend_sources = get_setting("min_trend_sources", "2")

    last_fetch = get_setting("last_news_fetch")
    last_send = get_setting("last_news_send")
    next_fetch = get_setting("next_news_fetch")
    next_trend = get_setting("next_trend_time")

    if next_fetch:
        next_dt = parse_datetime_with_tz(next_fetch)
        if next_dt:
            time_left = next_dt - now
            next_fetch_str = format_timedelta(time_left) + " دیگر"
        else:
            next_fetch_str = format_datetime_persian(next_fetch)
    else:
        next_fetch_str = "نامشخص"

    if next_trend:
        next_trend_str = format_datetime_persian(next_trend)
    else:
        next_trend_str = f"امشب ساعت {trend_hour}:{trend_minute}"

    rss_count = len(get_rss_sources())
    scrape_count = len(get_scrape_sources())

    msg = "📊 *وضعیت ربات خبری سینما*\n\n"

    msg += f"🕐 *زمان فعلی:* {now.strftime('%H:%M:%S')} (تهران)\n"
    msg += f"📅 {format_datetime_dual(now)}\n\n"

    msg += "⏰ *زمان‌بندی:*\n"
    msg += f"📰 جمع‌آوری بعدی: {next_fetch_str}\n"
    msg += f"   (بازه: هر {fetch_interval} ساعت)\n"
    msg += f"📊 ترند بعدی: {next_trend_str}\n"
    msg += f"   (حداقل {min_trend_sources} منبع)\n\n"

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
    print(get_status_message())
