import asyncio
import os
from datetime import datetime, time as dtime, timedelta
import pytz
import logging
import json

from telegram import Bot
from telegram.error import TelegramError, RetryAfter

from news_fetcher import fetch_all_news, DAILY_NEWS_DIR
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
TEHRAN_TZ = pytz.timezone('Asia/Tehran')


def now_tehran():
    return datetime.now(TEHRAN_TZ)


def get_daily_news_file():
    today = datetime.now().strftime("%Y%m%d")
    return os.path.join(DAILY_NEWS_DIR, f"daily_news_{today}.json")


async def send_daily_trend():
    """ارسال ترند روزانه از اخبار روزانه ذخیره‌شده"""
    logger.info("📊 شروع ارسال ترند روزانه...")
    TARGET_CHAT_ID = get_setting("TARGET_CHAT_ID")
    if not TARGET_CHAT_ID:
        logger.warning("⚠️ آیدی مقصد تنظیم نشده است.")
        return
    try:
        TARGET_CHAT_ID = int(TARGET_CHAT_ID)
    except ValueError:
        logger.error("❌ TARGET_CHAT_ID باید عدد صحیح باشد.")
        return

    daily_file = get_daily_news_file()
    if not os.path.exists(daily_file):
        logger.info("📭 فایل اخبار روزانه موجود نیست، ترند ارسال نشد.")
        return

    with open(daily_file, "r", encoding="utf-8") as f:
        daily_articles = json.load(f)

    min_sources = int(get_setting("min_trend_sources", 2))
    today = now_tehran().date().isoformat()
    trend_message = format_trend_message(today, min_sources=min_sources, daily_articles=daily_articles)

    if not trend_message:
        logger.info("📭 ترند روزانه خالی است، ارسال نشد.")
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
        # پاک کردن فایل روزانه بعد از ارسال
        os.remove(daily_file)
    except TelegramError as e:
        logger.error(f"❌ خطا در ارسال ترند: {e}")
