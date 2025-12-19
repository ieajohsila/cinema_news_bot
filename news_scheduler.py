"""
سرویس خبررسانی خودکار - Scheduler
"""

import asyncio
import os
from datetime import datetime, time as dtime, timedelta
import logging

from telegram import Bot
from telegram.error import TelegramError, RetryAfter

from news_fetcher import fetch_all_news
from news_ranker import rank_news, generate_daily_trend
from translation import translate_title
from category import classify_category
from database import get_setting, set_setting

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN تنظیم نشده است")

bot = Bot(token=BOT_TOKEN)

NEWS_FETCH_INTERVAL_HOURS = 3
DAILY_TREND_TIME = dtime(23, 55)


async def fetch_and_send_news():
    """هر N ساعت یکبار اخبار جدید را جمع‌آوری و رتبه‌بندی و ارسال می‌کند."""
    logger.info("\n" + "="*60)
    logger.info("⏰ شروع جمع‌آوری اخبار...")
    logger.info("="*60)
    
    # ذخیره زمان شروع
    start_time = datetime.now()
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
    for item in ranked:
        # ترجمه عنوان و خلاصه
        title_fa = translate_title(item['title'])
        summary_fa = translate_title(item.get('summary', '')[:300]) if item.get('summary') else ""
        
        # دسته‌بندی
        category = classify_category(item['title'], item.get('summary', ''))
        
        # ایموجی اهمیت
        importance_emoji = {
            3: "🔥🔥🔥",
            2: "⭐⭐",
            1: "⭐",
            0: "•"
        }.get(item.get('importance', 1), "⭐")
        
        # ساخت پیام
        msg = (
            f"{category}\n\n"
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
                logger.info(f"✅ ارسال شد (تلاش دوم): {title_fa[:40]}...")
            except Exception as e2:
                logger.error(f"❌ خطا در تلاش دوم: {e2}")
                
        except TelegramError as e:
            logger.error(f"❌ خطا در ارسال خبر: {e}")

    logger.info(f"✅ {sent_count} خبر با موفقیت ارسال شد.")
    
    # ذخیره زمان ارسال
    set_setting("last_news_send", datetime.now().isoformat())
    logger.info("="*60 + "\n")


async def send_daily_trend():
    """یک بار در روز ترند روزانه سینما را ارسال می‌کند."""
    logger.info("\n" + "="*60)
    logger.info("📊 شروع ارسال ترند روزانه...")
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

    # دریافت اخبار برای تحلیل
    all_news = fetch_all_news()
    trend_summary = generate_daily_trend(all_news)

    if not trend_summary or trend_summary == "امروز خبر جدیدی نبود.":
        logger.info("📭 ترند روزانه خالی است، ارسال نشد.")
        logger.info("="*60 + "\n")
        return

    try:
        await bot.send_message(
            chat_id=TARGET_CHAT_ID,
            text=trend_summary,
            parse_mode="Markdown",
        )
        logger.info("✅ ترند روزانه ارسال شد.")
    except TelegramError as e:
        logger.error(f"❌ خطا در ارسال ترند: {e}")
    
    logger.info("="*60 + "\n")


async def schedule_daily_trend():
    """زمان‌بندی دقیق ارسال ترند روزانه در ساعت مشخص."""
    while True:
        now = datetime.now()
        target_time = datetime.combine(now.date(), DAILY_TREND_TIME)

        if now >= target_time:
            target_time += timedelta(days=1)

        wait_seconds = (target_time - now).total_seconds()
        
        # ذخیره زمان بعدی
        set_setting("next_trend_time", target_time.isoformat())
        
        hours_left = wait_seconds / 3600
        logger.info(f"⏰ زمان باقی‌مانده تا ارسال ترند: {hours_left:.1f} ساعت")

        await asyncio.sleep(wait_seconds)
        await send_daily_trend()


async def schedule_news_fetching():
    """زمان‌بندی دوره‌ای دریافت اخبار."""
    while True:
        await fetch_and_send_news()
        
        # محاسبه زمان بعدی
        next_fetch = datetime.now() + timedelta(hours=NEWS_FETCH_INTERVAL_HOURS)
        set_setting("next_news_fetch", next_fetch.isoformat())
        
        logger.info(f"😴 خواب به مدت {NEWS_FETCH_INTERVAL_HOURS} ساعت...")
        logger.info(f"📅 دریافت بعدی: {next_fetch.strftime('%Y-%m-%d ساعت %H:%M')}\n")
        
        await asyncio.sleep(NEWS_FETCH_INTERVAL_HOURS * 3600)


async def run_scheduler():
    """اجرای همزمان دو وظیفه."""
    logger.info("\n" + "="*60)
    logger.info("🤖 سرویس خبررسانی خودکار سینما")
    logger.info("="*60)
    logger.info(f"⏰ دریافت اخبار: هر {NEWS_FETCH_INTERVAL_HOURS} ساعت")
    logger.info(f"📊 ارسال ترندها: روزانه ساعت {DAILY_TREND_TIME.strftime('%H:%M')}")
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
