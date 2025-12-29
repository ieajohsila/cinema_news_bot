"""
سرویس خبررسانی خودکار - Scheduler
با پشتیبانی از Timezone تهران
ذخیره اخبار روزانه و ارسال ترند
"""

import asyncio
import os
from datetime import datetime, time as dtime, timedelta
import pytz
import logging
import json

from telegram import Bot
from telegram.error import TelegramError, RetryAfter

from news_fetcher import fetch_all_news
from news_ranker import rank_news
from translation import translate_title
from category import classify_category
from trends import save_topic, format_trends_message, find_daily_trends

from database import get_setting, set_setting

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN تنظیم نشده است")

bot = Bot(token=BOT_TOKEN)
TEHRAN_TZ = pytz.timezone('Asia/Tehran')
DAILY_NEWS_DIR = "data/daily_news"
os.makedirs(DAILY_NEWS_DIR, exist_ok=True)


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


def get_daily_news_file():
    return os.path.join(DAILY_NEWS_DIR, now_tehran().strftime("%Y-%m-%d") + ".json")


def save_daily_news(news_list):
    file_path = get_daily_news_file()
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(news_list, f, ensure_ascii=False, indent=2)


def load_daily_news():
    file_path = get_daily_news_file()
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def clear_daily_news():
    file_path = get_daily_news_file()
    if os.path.exists(file_path):
        os.remove(file_path)
        logger.info(f"🗑️ فایل اخبار روزانه پاک شد: {file_path}")


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
        logger.error("❌ TARGET_CHAT_ID باید یک عدد صحیح باشد.")
        return

    min_importance_str = get_setting("min_importance") or "1"
    try:
        min_importance = int(min_importance_str)
    except ValueError:
        min_importance = 1

    all_news = fetch_all_news()
    if not all_news:
        logger.info("📭 هیچ خبر جدیدی یافت نشد.")
        return

    ranked = rank_news(all_news, min_importance=min_importance)
    if not ranked:
        logger.info(f"📭 هیچ خبری با اهمیت حداقل {min_importance} پیدا نشد.")
        return

    logger.info(f"📨 در حال ارسال {len(ranked)} خبر به کانال {TARGET_CHAT_ID}...")
    sent_count = 0
    daily_news = load_daily_news()
    
    for item in ranked:
        title_fa = translate_title(item['title'])
        summary_fa = translate_title(item.get('summary', '')[:300]) if item.get('summary') else ""
        category = classify_category(item['title'], item.get('summary', ''))
        category_hashtag = category.split()[1] if ' ' in category else category
        category_hashtag = f"#{category_hashtag}"
        importance_emoji = {3: "🔥🔥🔥", 2: "⭐⭐", 1: "⭐", 0: "•"}.get(item.get('importance', 1), "⭐")
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
            save_topic(item['title'], item['link'], item.get('source', 'unknown'))
            daily_news.append(item)
            logger.info(f"✅ ارسال شد: {title_fa[:40]}...")
            await asyncio.sleep(3)
        except RetryAfter as e:
            logger.warning(f"⏱️  Flood control: صبر {e.retry_after} ثانیه...")
            await asyncio.sleep(e.retry_after + 1)
            try:
                await bot.send_message(
                    chat_id=TARGET_CHAT_ID,
                    text=msg,
                    parse_mode="Markdown",
                    disable_web_page_preview=False,
                )
                sent_count += 1
                save_topic(item['title'], item['link'], item.get('source', 'unknown'))
                daily_news.append(item)
                logger.info(f"✅ ارسال شد (تلاش دوم): {title_fa[:40]}...")
            except Exception as e2:
                logger.error(f"❌ خطا در تلاش دوم: {e2}")
        except TelegramError as e:
            logger.error(f"❌ خطا در ارسال خبر: {e}")
    
    save_daily_news(daily_news)
    logger.info(f"✅ {sent_count} خبر با موفقیت ارسال شد.")
    set_setting("last_news_send", now_tehran().isoformat())


async def send_daily_trend():
    logger.info("\n" + "="*60)
    logger.info("📊 شروع ارسال ترند روزانه...")
    logger.info(f"🕐 زمان تهران: {now_tehran().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*60)
    
    TARGET_CHAT_ID = get_setting("TARGET_CHAT_ID")
    if not TARGET_CHAT_ID:
        logger.warning("⚠️  آیدی مقصد تنظیم نشده است.")
        return
    try:
        TARGET_CHAT_ID = int(TARGET_CHAT_ID)
    except ValueError:
        logger.error("❌ TARGET_CHAT_ID باید یک عدد صحیح باشد.")
        return

    min_sources = get_min_trend_sources()
    trends = find_daily_trends(min_sources=min_sources)
    if not trends:
        logger.info("📭 ترند روزانه خالی است، ارسال نشد.")
        return

    message = format_trends_message(trends)
    try:
        await bot.send_message(
            chat_id=TARGET_CHAT_ID,
            text=message,
            parse_mode="Markdown",
            disable_web_page_preview=True,
        )
        logger.info("✅ ترند روزانه ارسال شد.")
        set_setting("last_trend_send", now_tehran().isoformat())
        clear_daily_news()  # پاکسازی اخبار روزانه بعد از ارسال ترند
    except TelegramError as e:
        logger.error(f"❌ خطا در ارسال ترند: {e}")


async def schedule_daily_trend():
    while True:
        trend_time = get_trend_time()
        now = now_tehran()
        target_time = TEHRAN_TZ.localize(datetime.combine(now.date(), trend_time))
        if now >= target_time:
            target_time += timedelta(days=1)
        wait_seconds = (target_time - now).total_seconds()
        set_setting("next_trend_time", target_time.isoformat())
        hours_left = wait_seconds / 3600
        logger.info(f"⏰ زمان باقی‌مانده تا ارسال ترند: {hours_left:.1f} ساعت")
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
        logger.info("\n🛑 سرویس scheduler متوقف شد.")
    except Exception as e:
        logger.error(f"\n❌ خطا در scheduler: {e}")


if __name__ == "__main__":
    start_scheduler()
