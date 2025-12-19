"""
سرویس خبررسانی خودکار - Scheduler
با پشتیبانی از Timezone تهران
"""

import asyncio
import os
from datetime import datetime, time as dtime, timedelta
import pytz
import logging

from telegram import Bot
from telegram.error import TelegramError, RetryAfter

from news_fetcher import fetch_all_news
from news_ranker import rank_news
from translation import translate_title
from category import classify_category
from trends import save_topic, format_trend_message
from database import get_setting, set_setting

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN تنظیم نشده است")

bot = Bot(token=BOT_TOKEN)

# Timezone تهران
TEHRAN_TZ = pytz.timezone('Asia/Tehran')


def now_tehran():
    """دریافت زمان فعلی تهران"""
    return datetime.now(TEHRAN_TZ)


def get_fetch_interval():
    """دریافت بازه جمع‌آوری از تنظیمات (پیش‌فرض 3 ساعت)"""
    return int(get_setting("news_fetch_interval_hours", 3))


def get_trend_time():
    """دریافت زمان ارسال ترند (پیش‌فرض 23:55 به وقت تهران)"""
    trend_hour = int(get_setting("trend_hour", 23))
    trend_minute = int(get_setting("trend_minute", 55))
    return dtime(trend_hour, trend_minute)


def get_min_trend_sources():
    """حداقل منابع برای ترند (پیش‌فرض 2)"""
    return int(get_setting("min_trend_sources", 2))


async def fetch_and_send_news():
    """هر N ساعت یکبار اخبار جدید را جمع‌آوری و رتبه‌بندی و ارسال می‌کند."""
    logger.info("\n" + "="*60)
    logger.info("⏰ شروع جمع‌آوری اخبار...")
    logger.info(f"🕐 زمان تهران: {now_tehran().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*60)
    
    # ذخیره زمان شروع
    start_time = now_tehran()
    set_setting("last_news_fetch", start_time.isoformat())
    
    TARGET_CHAT_ID = get_setting("TARGET_CHAT_ID")

    if not TARGET_CHAT_ID:
        logger.warning("⚠️  آیدی مقصد تنظیم نشده است. لطفاً از پنل ادمین تنظیم کنید.")
        logger.info("="*60 + "\n")
        return

    try:
        TARGET_CHAT_ID = int(TARGET_CHAT_ID)
    except ValueError:
        logger.error("❌ TARGET_CHAT_ID باید یک عدد صحیح باشد.")
        logger.info("="*60 + "\n")
        return

    min_importance_str = get_setting("min_importance") or "1"
    try:
        min_importance = int(min_importance_str)
    except ValueError:
        min_importance = 1

    # جمع‌آوری اخبار
    all_news = fetch_all_news()
    
    if not all_news:
        logger.info("📭 هیچ خبر جدیدی یافت نشد.")
        logger.info("="*60 + "\n")
        return
    
    # رتبه‌بندی
    ranked = rank_news(all_news, min_importance=min_importance)

    if not ranked:
        logger.info(f"📭 هیچ خبری با اهمیت حداقل {min_importance} پیدا نشد.")
        logger.info("="*60 + "\n")
        return

    logger.info(f"📨 در حال ارسال {len(ranked)} خبر به کانال {TARGET_CHAT_ID}...")

    sent_count = 0
    today = now_tehran().date().isoformat()
    
    for item in ranked:
        # ترجمه عنوان و خلاصه
        title_fa = translate_title(item['title'])
        summary_fa = translate_title(item.get('summary', '')[:300]) if item.get('summary') else ""
        
        # دسته‌بندی
        category = classify_category(item['title'], item.get('summary', ''))
        
        # تبدیل دسته به هشتگ قابل جستجو
        category_hashtag = category.split()[1] if ' ' in category else category
        category_hashtag = f"#{category_hashtag}"
        
        # ایموجی اهمیت
        importance_emoji = {
            3: "🔥🔥🔥",
            2: "⭐⭐",
            1: "⭐",
            0: "•"
        }.get(item.get('importance', 1), "⭐")
        
        # ساخت پیام
        msg = (
            f"{category} {category_hashtag}\n\n"
            f"*{title_fa}*\n\n"
            f"{summary_fa}\n\n"
            f"🔗 [خبر اصلی]({item['link']})\n"
            f"{importance_emoji} اهمیت: {item.get('importance', 1)}/3"
        )
        
        try:
            await bot.send_message(
                chat_id=TARGET_CHAT_ID,
                text=msg,
                parse_mode="Markdown",
                disable_web_page_preview=False,
            )
            sent_count += 1
            
            # ذخیره برای ترند
            save_topic(
                title=item['title'],
                link=item['link'],
                source=item.get('source', 'unknown'),
                date=today
            )
            
            logger.info(f"✅ ارسال شد: {title_fa[:40]}...")
            await asyncio.sleep(3)  # تاخیر برای جلوگیری از Flood
            
        except RetryAfter as e:
            logger.warning(f"⏱️  Flood control: صبر {e.retry_after} ثانیه...")
            await asyncio.sleep(e.retry_after + 1)
            
            # تلاش مجدد
            try:
                await bot.send_message(
                    chat_id=TARGET_CHAT_ID,
                    text=msg,
                    parse_mode="Markdown",
                    disable_web_page_preview=False,
                )
                sent_count += 1
                save_topic(item['title'], item['link'], item.get('source', 'unknown'), today)
                logger.info(f"✅ ارسال شد (تلاش دوم): {title_fa[:40]}...")
            except Exception as e2:
                logger.error(f"❌ خطا در تلاش دوم: {e2}")
                
        except TelegramError as e:
            logger.error(f"❌ خطا در ارسال خبر: {e}")

    logger.info(f"✅ {sent_count} خبر با موفقیت ارسال شد.")
    
    # ذخیره زمان ارسال
    set_setting("last_news_send", now_tehran().isoformat())
    logger.info("="*60 + "\n")


async def send_daily_trend():
    """یک بار در روز ترند روزانه سینما را ارسال می‌کند."""
    logger.info("\n" + "="*60)
    logger.info("📊 شروع ارسال ترند روزانه...")
    logger.info(f"🕐 زمان تهران: {now_tehran().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*60)
    
    TARGET_CHAT_ID = get_setting("TARGET_CHAT_ID")

    if not TARGET_CHAT_ID:
        logger.warning("⚠️  آیدی مقصد تنظیم نشده است.")
        logger.info("="*60 + "\n")
        return

    try:
        TARGET_CHAT_ID = int(TARGET_CHAT_ID)
    except ValueError:
        logger.error("❌ TARGET_CHAT_ID باید یک عدد صحیح باشد.")
        logger.info("="*60 + "\n")
        return

    # دریافت حداقل منابع از تنظیمات
    min_sources = get_min_trend_sources()
    
    # تاریخ امروز به وقت تهران
    today = now_tehran().date().isoformat()
    
    # ساخت پیام ترند
    trend_message = format_trend_message(today, min_sources=min_sources)

    if not trend_message:
        logger.info("📭 ترند روزانه خالی است، ارسال نشد.")
        logger.info("="*60 + "\n")
        return

    try:
        await bot.send_message(
            chat_id=TARGET_CHAT_ID,
            text=trend_message,
            parse_mode="Markdown",
            disable_web_page_preview=True,
        )
        logger.info("✅ ترند روزانه ارسال شد.")
        set_setting("last_trend_send", now_tehran().isoformat())
    except TelegramError as e:
        logger.error(f"❌ خطا در ارسال ترند: {e}")
    
    logger.info("="*60 + "\n")


async def schedule_daily_trend():
    """زمان‌بندی دقیق ارسال ترند روزانه در ساعت مشخص (به وقت تهران)."""
    while True:
        trend_time = get_trend_time()
        now = now_tehran()
        
        # ساخت datetime با timezone تهران
        target_time = TEHRAN_TZ.localize(
            datetime.combine(now.date(), trend_time)
        )

        if now >= target_time:
            # اگر زمان گذشته، برای فردا تنظیم کن
            target_time += timedelta(days=1)

        wait_seconds = (target_time - now).total_seconds()
        
        # ذخیره زمان بعدی
        set_setting("next_trend_time", target_time.isoformat())
        
        hours_left = wait_seconds / 3600
        logger.info(f"⏰ زمان باقی‌مانده تا ارسال ترند: {hours_left:.1f} ساعت")
        logger.info(f"📅 ترند بعدی: {target_time.strftime('%Y-%m-%d %H:%M')} (تهران)")

        await asyncio.sleep(wait_seconds)
        await send_daily_trend()


async def schedule_news_fetching():
    """زمان‌بندی دوره‌ای دریافت اخبار."""
    while True:
        await fetch_and_send_news()
        
        # دریافت بازه از تنظیمات
        interval_hours = get_fetch_interval()
        
        # محاسبه زمان بعدی (به وقت تهران)
        next_fetch = now_tehran() + timedelta(hours=interval_hours)
        set_setting("next_news_fetch", next_fetch.isoformat())
        
        logger.info(f"😴 خواب به مدت {interval_hours} ساعت...")
        logger.info(f"📅 دریافت بعدی: {next_fetch.strftime('%Y-%m-%d %H:%M')} (تهران)\n")
        
        await asyncio.sleep(interval_hours * 3600)


async def run_scheduler():
    """اجرای همزمان دو وظیفه."""
    logger.info("\n" + "="*60)
    logger.info("🤖 سرویس خبررسانی خودکار سینما")
    logger.info(f"🌍 Timezone: تهران (UTC+3:30)")
    logger.info(f"🕐 زمان فعلی: {now_tehran().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*60)
    
    interval_hours = get_fetch_interval()
    trend_time = get_trend_time()
    
    logger.info(f"⏰ دریافت اخبار: هر {interval_hours} ساعت")
    logger.info(f"📊 ارسال ترندها: روزانه ساعت {trend_time.strftime('%H:%M')} (تهران)")
    logger.info("🛑 برای توقف: CTRL+C")
    logger.info("="*60 + "\n")
    
    await asyncio.gather(
        schedule_news_fetching(),
        schedule_daily_trend(),
    )


def start_scheduler():
    """تابع ورودی برای استفاده در Thread - برای main.py"""
    try:
        asyncio.run(run_scheduler())
    except KeyboardInterrupt:
        logger.info("\n🛑 سرویس scheduler متوقف شد.")
    except Exception as e:
        logger.error(f"\n❌ خطا در scheduler: {e}")


# اجرای مستقیم
if __name__ == "__main__":
    start_scheduler()
