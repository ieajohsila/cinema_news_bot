"""
Scheduler بدون باگ با:
1. mark_sent فقط بعد از ارسال موفق
2. ذخیره اخبار در فایل روزانه
3. جلوگیری از تکرار کامل
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
from database import (
    get_setting, set_setting, 
    save_collected_news, mark_sent, 
    save_topic
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN تنظیم نشده")

bot = Bot(token=BOT_TOKEN)

TEHRAN_TZ = pytz.timezone('Asia/Tehran')


def now_tehran():
    return datetime.now(TEHRAN_TZ)


def get_fetch_interval():
    return int(get_setting("news_fetch_interval_hours", 3))


def get_trend_time():
    hour = int(get_setting("trend_hour", 23))
    minute = int(get_setting("trend_minute", 55))
    return dtime(hour, minute)


async def fetch_and_send_news():
    """جمع‌آوری و ارسال اخبار با ذخیره صحیح"""
    logger.info("\n" + "="*60)
    logger.info("⏰ شروع جمع‌آوری اخبار")
    logger.info(f"🕐 {now_tehran().strftime('%Y-%m-%d %H:%M:%S')} تهران")
    logger.info("="*60)
    
    start_time = now_tehran()
    set_setting("last_news_fetch", start_time.isoformat())
    
    TARGET_CHAT_ID = get_setting("TARGET_CHAT_ID")
    
    if not TARGET_CHAT_ID:
        logger.warning("⚠️ کانال مقصد تنظیم نشده")
        logger.info("="*60 + "\n")
        return
    
    try:
        TARGET_CHAT_ID = int(TARGET_CHAT_ID)
    except ValueError:
        logger.error("❌ TARGET_CHAT_ID نامعتبر")
        logger.info("="*60 + "\n")
        return
    
    min_importance = int(get_setting("min_importance", "1"))
    
    # جمع‌آوری
    all_news = fetch_all_news()
    
    if not all_news:
        logger.info("📭 خبر جدیدی نیست")
        logger.info("="*60 + "\n")
        return
    
    # رتبه‌بندی
    ranked = rank_news(all_news, min_importance=min_importance)
    
    if not ranked:
        logger.info(f"📭 خبری با اهمیت {min_importance}+ نیست")
        logger.info("="*60 + "\n")
        return
    
    # ذخیره در collected_news
    save_collected_news(ranked)
    logger.info(f"💾 {len(ranked)} خبر در collected_news.json ذخیره شد")
    
    logger.info(f"📨 ارسال {len(ranked)} خبر به {TARGET_CHAT_ID}...")
    
    sent_count = 0
    today = now_tehran().date().isoformat()
    
    for item in ranked:
        # ترجمه
        title_fa = translate_title(item['title'])
        summary = item.get('summary', '')
        summary_fa = translate_title(summary[:300]) if summary else ""
        
        # دسته‌بندی
        category = classify_category(item['title'], summary)
        category_tag = category.split()[1] if ' ' in category else category
        category_tag = f"#{category_tag}"
        
        # ایموجی
        importance = item.get('importance', 1)
        emoji_map = {3: "🔥🔥🔥", 2: "⭐⭐", 1: "⭐", 0: "•"}
        importance_emoji = emoji_map.get(importance, "⭐")
        
        # پیام
        msg = (
            f"{category} {category_tag}\n\n"
            f"*{title_fa}*\n\n"
            f"{summary_fa}\n\n"
            f"🔗 [خبر اصلی]({item['link']})\n"
            f"{importance_emoji} اهمیت: {importance}/3"
        )
        
        try:
            await bot.send_message(
                chat_id=TARGET_CHAT_ID,
                text=msg,
                parse_mode="Markdown",
                disable_web_page_preview=False,
            )
            
            sent_count += 1
            
            # ✅ فقط الان mark کن
            mark_sent(item['link'])
            
            # ذخیره برای ترند
            save_topic(
                topic=item['title'],
                link=item['link'],
                source=item.get('source', 'unknown'),
                date=today
            )
            
            logger.info(f"✅ ارسال: {title_fa[:40]}...")
            await asyncio.sleep(3)
            
        except RetryAfter as e:
            logger.warning(f"⏱️ Flood: صبر {e.retry_after}s")
            await asyncio.sleep(e.retry_after + 1)
            
            try:
                await bot.send_message(
                    chat_id=TARGET_CHAT_ID,
                    text=msg,
                    parse_mode="Markdown",
                    disable_web_page_preview=False,
                )
                sent_count += 1
                mark_sent(item['link'])
                save_topic(
                    topic=item['title'],
                    link=item['link'],
                    source=item.get('source', 'unknown'),
                    date=today
                )
                logger.info(f"✅ ارسال (تلاش 2): {title_fa[:40]}...")
            except Exception as e2:
                logger.error(f"❌ تلاش دوم: {e2}")
                
        except TelegramError as e:
            logger.error(f"❌ خطای تلگرام: {e}")
    
    logger.info(f"✅ {sent_count} خبر ارسال شد")
    set_setting("last_news_send", now_tehran().isoformat())
    logger.info("="*60 + "\n")


async def send_daily_trend():
    """ارسال ترند روزانه"""
    logger.info("\n" + "="*60)
    logger.info("📊 ارسال ترند روزانه")
    logger.info(f"🕐 {now_tehran().strftime('%Y-%m-%d %H:%M:%S')} تهران")
    logger.info("="*60)
    
    TARGET_CHAT_ID = get_setting("TARGET_CHAT_ID")
    
    if not TARGET_CHAT_ID:
        logger.warning("⚠️ کانال تنظیم نشده")
        logger.info("="*60 + "\n")
        return
    
    try:
        TARGET_CHAT_ID = int(TARGET_CHAT_ID)
    except ValueError:
        logger.error("❌ TARGET_CHAT_ID نامعتبر")
        logger.info("="*60 + "\n")
        return
    
    from database import daily_trends
    
    today = now_tehran().date().isoformat()
    trends = daily_trends(today)
    
    if not trends:
        logger.info("📭 ترندی نیست")
        logger.info("="*60 + "\n")
        return
    
    msg = "📈 *ترندهای امروز سینما*\n\n"
    msg += f"📅 {today}\n\n"
    
    for i, trend in enumerate(trends[:10], 1):
        emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}️⃣"
        
        msg += f"{emoji} *{trend['topic'][:80]}*\n"
        msg += f"   📰 {', '.join(trend['sources'][:3])}\n"
        
        if len(trend['sources']) > 3:
            msg += f"   ➕ و {len(trend['sources']) - 3} منبع\n"
        
        if trend['links'] and trend['links'][0]:
            msg += f"   🔗 [مشاهده]({trend['links'][0]})\n"
        
        msg += "\n"
    
    msg += "━━━━━━━━━━━━━━━━━\n"
    msg += f"🔥 {len(trends)} ترند\n"
    msg += f"⏰ {now_tehran().strftime('%H:%M')}"
    
    try:
        await bot.send_message(
            chat_id=TARGET_CHAT_ID,
            text=msg,
            parse_mode='Markdown',
            disable_web_page_preview=True,
        )
        logger.info("✅ ترند ارسال شد")
        set_setting("last_trend_send", now_tehran().isoformat())
    except TelegramError as e:
        logger.error(f"❌ خطای ترند: {e}")
    
    logger.info("="*60 + "\n")


async def schedule_daily_trend():
    """زمان‌بندی ترند روزانه"""
    while True:
        trend_time = get_trend_time()
        now = now_tehran()
        
        target_time = TEHRAN_TZ.localize(
            datetime.combine(now.date(), trend_time)
        )
        
        if now >= target_time:
            target_time += timedelta(days=1)
        
        wait_seconds = (target_time - now).total_seconds()
        
        set_setting("next_trend_time", target_time.isoformat())
        
        hours = wait_seconds / 3600
        logger.info(f"⏰ ترند بعدی: {hours:.1f} ساعت دیگر")
        logger.info(f"📅 {target_time.strftime('%Y-%m-%d %H:%M')} تهران")
        
        await asyncio.sleep(wait_seconds)
        await send_daily_trend()


async def schedule_news_fetching():
    """زمان‌بندی دریافت اخبار"""
    while True:
        await fetch_and_send_news()
        
        interval = get_fetch_interval()
        next_fetch = now_tehran() + timedelta(hours=interval)
        set_setting("next_news_fetch", next_fetch.isoformat())
        
        logger.info(f"😴 خواب {interval} ساعت")
        logger.info(f"📅 بعدی: {next_fetch.strftime('%Y-%m-%d %H:%M')} تهران\n")
        
        await asyncio.sleep(interval * 3600)


async def run_scheduler():
    """اجرای همزمان"""
    logger.info("\n" + "="*60)
    logger.info("🤖 سرویس خبررسانی")
    logger.info(f"🌍 Timezone: تهران")
    logger.info(f"🕐 {now_tehran().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*60)
    
    interval = get_fetch_interval()
    trend_time = get_trend_time()
    
    logger.info(f"⏰ دریافت: هر {interval} ساعت")
    logger.info(f"📊 ترند: {trend_time.strftime('%H:%M')} روزانه")
    logger.info("🛑 توقف: CTRL+C")
    logger.info("="*60 + "\n")
    
    await asyncio.gather(
        schedule_news_fetching(),
        schedule_daily_trend(),
    )


def start_scheduler():
    """ورودی Thread"""
    try:
        asyncio.run(run_scheduler())
    except KeyboardInterrupt:
        logger.info("\n🛑 scheduler متوقف شد")
    except Exception as e:
        logger.error(f"\n❌ خطا: {e}")


if __name__ == "__main__":
    start_scheduler()
