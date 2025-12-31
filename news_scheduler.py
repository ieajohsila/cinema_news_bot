"""
سرویس خبررسانی خودکار - Scheduler
با پشتیبانی از Timezone تهران
"""

import asyncio
import os
import html
import re
from datetime import datetime, time as dtime, timedelta
import pytz
import logging
from telegram import Bot
from telegram.error import TelegramError, RetryAfter

from news_fetcher import fetch_all_news
from translation import translate_title
from category import classify_category
from news_ranker import rank_news
from trends import save_topic, find_daily_trends, format_trends_message, save_daily_news
from database import get_setting, set_setting, is_sent, mark_sent

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# 🔧 FIX: استفاده صحیح از os.getenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN تنظیم نشده است")

bot = Bot(token=BOT_TOKEN)

# Timezone تهران
TEHRAN_TZ = pytz.timezone('Asia/Tehran')


def now_tehran():
    return datetime.now(TEHRAN_TZ)


def get_fetch_interval():
    # 🔧 FIX: تبدیل به int بعد از دریافت string
    return int(get_setting("news_fetch_interval_hours", "3"))


def get_trend_time():
    # 🔧 FIX: تبدیل به int بعد از دریافت string
    trend_hour = int(get_setting("trend_hour", "23"))
    trend_minute = int(get_setting("trend_minute", "55"))
    return dtime(trend_hour, trend_minute)


def get_min_trend_sources():
    # 🔧 FIX: تبدیل به int بعد از دریافت string
    return int(get_setting("min_trend_sources", "2"))


def clean_text(text):
    """
    🔧 FIX: تمیز کردن متن از HTML entities و کاراکترهای مزاحم
    """
    if not text:
        return ""
    
    # Decode HTML entities
    text = html.unescape(text)
    
    # حذف تگ‌های HTML
    text = re.sub(r'<[^>]+>', '', text)
    
    # حذف فضای خالی اضافی
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def is_valid_news(item):
    """
    🔧 FIX: بررسی اینکه آیتم یک خبر واقعی است یا لینک RSS
    """
    title = item.get('title', '').lower()
    link = item.get('link', item.get('url', '')).lower()
    
    # فیلتر لینک‌های RSS
    if '/feed' in link or '/rss' in link:
        return False
    
    # فیلتر عناوین خالی یا خیلی کوتاه
    if not title or len(title.strip()) < 10:
        return False
    
    # فیلتر عناوین که فقط نام سایت هستن
    invalid_titles = [
        'latest news', 'آخرین اخبار', 'home', 'feed',
        'rss', 'cinema', 'movies', 'news'
    ]
    if title.strip() in invalid_titles:
        return False
    
    return True


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

    # 🔧 FIX: تبدیل به int بعد از دریافت string
    min_importance = int(get_setting("min_importance", "1"))
    logger.info(f"⭐ حداقل اهمیت: {min_importance}")

    try:
        all_news = fetch_all_news()
        if not all_news:
            logger.info("📭 هیچ خبر جدیدی یافت نشد.")
            return

        # 🔧 FIX: فیلتر کردن اخبار نامعتبر
        valid_news = [item for item in all_news if is_valid_news(item)]
        logger.info(f"✅ {len(valid_news)} خبر معتبر از {len(all_news)} آیتم")

        if not valid_news:
            logger.info("📭 هیچ خبر معتبری یافت نشد.")
            return

        # 🔧 FIX: رتبه‌بندی اخبار بر اساس اهمیت
        ranked_news = rank_news(valid_news, min_importance=min_importance)
        logger.info(f"🎯 {len(ranked_news)} خبر با اهمیت حداقل {min_importance}")

        if not ranked_news:
            logger.info(f"📭 هیچ خبری با اهمیت حداقل {min_importance} یافت نشد.")
            return

        sent_count = 0
        skipped_count = 0
        
        for item in ranked_news:
            # بررسی تکراری نبودن
            link = item.get('link', item.get('url', ''))
            if not link:
                logger.warning(f"⚠️ خبر بدون لینک: {item.get('title', 'بدون عنوان')}")
                continue
            
            # چک کردن ارسال قبلی
            news_id = hash(link)
            if is_sent(str(news_id)):
                skipped_count += 1
                continue
            
            # 🔧 FIX: تمیز کردن متن‌ها
            title_clean = clean_text(item['title'])
            summary_clean = clean_text(item.get('summary', '')[:300])
            
            # ترجمه
            title_fa = translate_title(title_clean)
            summary_fa = translate_title(summary_clean) if summary_clean else ""
            
            # دسته‌بندی
            category = classify_category(title_clean, summary_clean)
            category_hashtag = f"#{category.split()[1]}" if ' ' in category else f"#{category}"
            
            # ایموجی اهمیت
            importance = item.get('importance', 1)
            importance_emoji = {3:"🔥🔥🔥", 2:"⭐⭐", 1:"⭐", 0:"•"}.get(importance, "⭐")
            
            msg = (
                f"{category} {category_hashtag}\n\n"
                f"*{title_fa}*\n\n"
                f"{summary_fa}\n\n"
                f"🔗 [خبر اصلی]({link})\n"
                f"{importance_emoji} اهمیت: {importance}/3"
            )
            
            try:
                await bot.send_message(
                    chat_id=TARGET_CHAT_ID,
                    text=msg,
                    parse_mode="Markdown",
                    disable_web_page_preview=False
                )
                
                # ثبت ارسال شده
                mark_sent(str(news_id))
                sent_count += 1
                
                # 🔧 FIX: ذخیره خبر در فایل روزانه برای تحلیل ترند
                save_daily_news(item)
                
                # ذخیره در ترندها
                save_topic(title_clean, link, item.get('source','unknown'))
                
                logger.info(f"✅ ارسال شد: {title_fa[:40]}... (اهمیت: {importance})")
                await asyncio.sleep(2)
                
            except RetryAfter as e:
                logger.warning(f"⏱️ Flood control: صبر {e.retry_after} ثانیه...")
                await asyncio.sleep(e.retry_after + 1)
            except TelegramError as e:
                logger.error(f"❌ خطا در ارسال خبر: {e}")
            except Exception as e:
                logger.error(f"❌ خطای غیرمنتظره: {e}")

        logger.info(f"✅ {sent_count} خبر ارسال شد | {skipped_count} خبر تکراری رد شد")
        set_setting("last_news_send", now_tehran().isoformat())
        logger.info("="*60 + "\n")
        
    except Exception as e:
        logger.error(f"❌ خطای کلی در fetch_and_send_news: {e}")
        import traceback
        logger.error(traceback.format_exc())


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
        try:
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
        except Exception as e:
            logger.error(f"❌ خطا در schedule_daily_trend: {e}")
            await asyncio.sleep(3600)


async def schedule_news_fetching():
    while True:
        try:
            await fetch_and_send_news()
            interval_hours = get_fetch_interval()
            next_fetch = now_tehran() + timedelta(hours=interval_hours)
            set_setting("next_news_fetch", next_fetch.isoformat())
            logger.info(f"😴 خواب به مدت {interval_hours} ساعت...")
            await asyncio.sleep(interval_hours * 3600)
        except Exception as e:
            logger.error(f"❌ خطا در schedule_news_fetching: {e}")
            await asyncio.sleep(3600)


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
