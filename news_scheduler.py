import asyncio
import os
from datetime import datetime, time as dtime, timedelta
import logging

from telegram import Bot
from telegram.error import TelegramError

from news_fetcher import fetch_all_news
from news_ranker import rank_news, generate_daily_trend
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
    logger.info("⏰ شروع جمع‌آوری اخبار...")
    
    # ذخیره زمان شروع
    start_time = datetime.now()
    set_setting("last_news_fetch", start_time.isoformat())
    
    TARGET_CHAT_ID = get_setting("TARGET_CHAT_ID")

    if not TARGET_CHAT_ID:
        logger.warning("⚠️  آیدی مقصد تنظیم نشده است. لطفاً از پنل ادمین تنظیم کنید.")
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
    ranked = rank_news(all_news, min_importance=min_importance)

    if not ranked:
        logger.info("📭 خبر جدیدی برای ارسال پیدا نشد.")
        return

    logger.info(f"📨 در حال ارسال {len(ranked)} خبر به {TARGET_CHAT_ID}...")

    sent_count = 0
    for item in ranked:
        msg = (
            f"📰 *{item['title']}*\n\n"
            f"{item.get('summary', '')}\n\n"
            f"🔗 [مطالعه بیشتر]({item['link']})\n"
            f"⭐️ اهمیت: {item['importance']}/3"
        )
        try:
            await bot.send_message(
                chat_id=TARGET_CHAT_ID,
                text=msg,
                parse_mode="Markdown",
                disable_web_page_preview=False,
            )
            sent_count += 1
            await asyncio.sleep(2)
        except TelegramError as e:
            logger.error(f"خطا در ارسال خبر: {e}")

    logger.info(f"✅ {sent_count} خبر با موفقیت ارسال شد.")
    
    # ذخیره زمان ارسال
    set_setting("last_news_send", datetime.now().isoformat())


async def send_daily_trend():
    """یک بار در روز ترند روزانه سینما را ارسال می‌کند."""
    logger.info("📊 شروع ارسال ترند روزانه...")
    
    TARGET_CHAT_ID = get_setting("TARGET_CHAT_ID")

    if not TARGET_CHAT_ID:
        logger.warning("⚠️  آیدی مقصد تنظیم نشده است.")
        return

    try:
        TARGET_CHAT_ID = int(TARGET_CHAT_ID)
    except ValueError:
        logger.error("❌ TARGET_CHAT_ID باید یک عدد صحیح باشد.")
        return

    all_news = fetch_all_news()
    trend_summary = generate_daily_trend(all_news)

    if not trend_summary or trend_summary == "امروز خبر جدیدی نبود.":
        logger.info("📭 ترند روزانه خالی است، ارسال نشد.")
        return

    try:
        await bot.send_message(
            chat_id=TARGET_CHAT_ID,
            text=f"📊 *ترند روزانه سینما*\n\n{trend_summary}",
            parse_mode="Markdown",
        )
        logger.info("✅ ترند روزانه ارسال شد.")
    except TelegramError as e:
        logger.error(f"خطا در ارسال ترند: {e}")


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
        
        logger.info(f"⏰ خواب به مدت {NEWS_FETCH_INTERVAL_HOURS} ساعت...")
        logger.info(f"📅 دریافت بعدی: {next_fetch.strftime('%Y-%m-%d %H:%M')}")
        
        await asyncio.sleep(NEWS_FETCH_INTERVAL_HOURS * 3600)


async def main():
    """اجرای همزمان دو وظیفه."""
    logger.info("🚀 سرویس خبررسانی خودکار سینما راه‌اندازی شد")
    logger.info(f"⏰ دریافت اخبار: هر {NEWS_FETCH_INTERVAL_HOURS} ساعت")
    logger.info(f"📊 ارسال ترندها: روزانه ساعت {DAILY_TREND_TIME.strftime('%H:%M')}")
    logger.info("🛑 برای توقف: CTRL+C")
    
    await asyncio.gather(
        schedule_news_fetching(),
        schedule_daily_trend(),
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n🛑 سرویس متوقف شد.")
