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
from translation import translate_title
from category import classify_category
from trends import save_topic, find_daily_trends, format_trends_message
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
    return datetime.now(TEHRAN_TZ)


def get_fetch_interval():
    return int(get_setting("news_fetch_interval_hours", 3))


def get_trend_time():
    trend_hour = int(get_setting("trend_hour", 23))
    trend_minute = int(get_setting("trend_minute", 55))
    return dtime(trend_hour, trend_minute)


def get_min_trend_sources():
    return int(get_setting("min_trend_sources", 2))


async def fetch_and_send_news():
    logger.info("\n" + "="*60)
    logger.info("⏰ شروع جمع‌آوری اخبار...")
    logger.info(f"🕐 زمان تهران: {now_tehran().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*60)

    start_time = now_tehran()
    set_setting("last_news_fetch", start_time.isoformat())
    TARGET_CHAT_ID = get_setting("TARGET_CHAT_ID")
    if not TARGET_CHAT_ID:
        logger.warning("⚠️  آیدی مقصد تنظیم نشده است.")
        return
    try:
        TARGET_CHAT_ID = int(TARGET_CHAT_ID)
    except ValueError:
        logger.error("❌ TARGET_CHAT_ID باید عدد صحیح باشد.")
        return

    min_importance = int(get_setting("min_importance", 1))

    all_news = fetch_all_news()
    if not all_news:
        logger.info("📭 هیچ خبر جدیدی یافت نشد.")
        return

    sent_count = 0
    today_str = now_tehran().strftime("%Y-%m-%d")
    for item in all_news:
        title_fa = translate_title(item['title'])
        summary_fa = translate_title(item.get('summary', '')[:300]) if item.get('summary') else ""
        category = classify_category(item['title'], item.get('summary', ''))
        category_hashtag = f"#{category.split()[1]}" if ' ' in category else f"#{category}"
        importance_emoji = {3:"🔥🔥🔥",2:"⭐⭐",1:"⭐",0:"•"}.get(item.get('importance',1),"⭐")
        msg = (
            f"{category} {category_hashtag}\n\n"
            f"*{title_fa}*\n\n"
            f"{summary_fa}\n\n"
            f"🔗 [خبر اصلی]({item['link']})\n"
            f"{importance_emoji} اهمیت: {item.get('importance',1)}/3"
        )
        try:
            await bot.send_message(
                chat_id=TARGET_CHAT_ID,
                text=msg,
                parse_mode="Markdown",
                disable_web_page_preview=False
            )
            sent_count += 1
            save_topic(item['title'], item['url'], item.get('source','unknown'))
            logger.info(f"✅ ارسال شد: {title_fa[:40]}...")
            await asyncio.sleep(2)
        except RetryAfter as e:
            logger.warning(f"⏱️ Flood control: صبر {e.retry_after} ثانیه...")
            await asyncio.sleep(e.retry_after + 1)
        except TelegramError as e:
            logger.error(f"❌ خطا در ارسال خبر: {e}")

    logger.info(f"✅ {sent_count} خبر با موفقیت ارسال شد.")
    set_setting("last_news_send", now_tehran().isoformat())
    logger.info("="*60 + "\n")


async def send_daily_trend():
    logger.info("\n" + "="*60)
    logger.info("📊 شروع ارسال ترند روزانه...")
    TARGET_CHAT_ID = get_setting("TARGET_CHAT_ID")
    if not TARGET_CHAT_ID:
        logger.warning("⚠️  آیدی مقصد تنظیم نشده است.")
        return
    try:
        TARGET_CHAT_ID = int(TARGET_CHAT_ID)
    except ValueError:
        logger.error("❌ TARGET_CHAT_ID باید عدد صحیح باشد.")
        return

    min_sources = get_min_trend_sources()
    trends = find_daily_trends(min_sources=min_sources)
    trend_message = format_trends_message(trends)

    if not trend_message:
        logger.info("📭 ترند روزانه خالی است، ارسال نشد.")
        return

    try:
        await bot.send_message(
            chat_id=TARGET_CHAT_ID,
            text=trend_message,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )
        logger.info("✅ ترند روزانه ارسال شد.")
        set_setting("last_trend_send", now_tehran().isoformat())
    except TelegramError as e:
        logger.error(f"❌ خطا در ارسال ترند: {e}")

    logger.info("="*60 + "\n")


async def schedule_daily_trend():
    while True:
        trend_time = get_trend_time()
        now = now_tehran()
        target_time = TEHRAN_TZ.localize(datetime.combine(now.date(), trend_time))
        if now >= target_time:
            target_time += timedelta(days=1)
        wait_seconds = (target_time - now).total_seconds()
        set_setting("next_trend_time", target_time.isoformat())
        logger.info(f"⏰ زمان باقی‌مانده تا ارسال ترند: {wait_seconds/3600:.1f} ساعت")
        await asyncio.sleep(wait_seconds)
        await send_daily_trend()


async def schedule_news_fetching():
    while True:
        await fetch_and_send_news()
        interval_hours = get_fetch_interval()
        next_fetch = now_tehran() + timedelta(hours=interval_hours)
        set_setting("next_news_fetch", next_fetch.isoformat())
        logger.info(f"😴 خواب به مدت {interval_hours} ساعت...")
        await asyncio.sleep(interval_hours * 3600)


async def run_scheduler():
    logger.info("\n" + "="*60)
    logger.info("🤖 سرویس خبررسانی خودکار سینما")
    logger.info(f"🌍 Timezone: تهران (UTC+3:30)")
    logger.info(f"🕐 زمان فعلی: {now_tehran().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*60 + "\n")
    await asyncio.gather(
        schedule_news_fetching(),
        schedule_daily_trend(),
    )


def start_scheduler():
    try:
        asyncio.run(run_scheduler())
    except KeyboardInterrupt:
        logger.info("🛑 سرویس scheduler متوقف شد.")
    except Exception as e:
        logger.error(f"❌ خطا در scheduler: {e}")


if __name__ == "__main__":
    start_scheduler()
