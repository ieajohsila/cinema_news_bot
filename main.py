import os
import feedparser
from telegram import Bot
from datetime import date, datetime, timedelta
import time
from threading import Thread

from scrapers import extract_article
from translator import fa
from importance import classify_importance
from category import classify_category
from database import is_sent, mark_sent, get_setting
from trends import save_topic, daily_trends
from rss_sources import DEFAULT_RSS_SOURCES

BOT_TOKEN = os.getenv("BOT_TOKEN")  # حالا درست کار می‌کنه
bot = Bot(BOT_TOKEN)


def send_news(chat_id, title, summary, image, d, site, link):
    category = classify_category(title, summary)
    importance = classify_importance(title, summary)
    min_level = int(get_setting("min_importance", 1))

    if importance < min_level:
        return  # فیلتر سطح اهمیت

    caption = (
        f"{category}\n\n"
        f"*{fa(title)}*\n\n"
        f"{fa(summary)}\n\n"
        f"📅 {d}\n"
        f"🌐 {site}\n\n"
        f"🔗 [خبر اصلی]({link})"
    )

    if image:
        bot.send_photo(chat_id=chat_id, photo=image, caption=caption, parse_mode="Markdown")
    else:
        bot.send_message(chat_id=chat_id, text=caption, parse_mode="Markdown")

    mark_sent(link)
    save_topic(title, site, d)


def fetch_and_send():
    chat_id = get_setting("TARGET_CHAT_ID")
    if not chat_id:
        print("⚠️ آیدی مقصد تنظیم نشده است.")
        return

    for src in RSS_SOURCES:
        feed = feedparser.parse(src["url"])
        for entry in feed.entries[:5]:
            if is_sent(entry.link):
                continue
            try:
                title, summary, image, d, site = extract_article(entry.link)
                send_news(chat_id, title, summary, image, d, site, entry.link)
            except Exception as e:
                print(f"Error processing {entry.link}: {e}")


def send_daily_trends():
    chat_id = get_setting("TARGET_CHAT_ID")
    today = date.today().isoformat()
    trends = daily_trends(today)
    if not trends:
        return

    msg = "📊 *ترندهای امروز سینما*\n\n"
    for topic, count in trends:
        msg += f"🔥 {topic} ({count} منبع)\n"

    bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")


def schedule_news(interval_hours=3):
    """
    اجرای دوره‌ای اخبار هر 'interval_hours' ساعت یکبار
    """
    while True:
        print(f"[{datetime.now()}] جمع‌آوری و ارسال اخبار آغاز شد.")
        fetch_and_send()
        print(f"[{datetime.now()}] پایان ارسال اخبار. خواب به مدت {interval_hours} ساعت...")
        time.sleep(interval_hours * 3600)


def schedule_daily_trends(hour=23, minute=55):
    """
    ارسال ترند روزانه ساعت مشخص (پیش‌فرض 23:55)
    """
    while True:
        now = datetime.now()
        send_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if send_time < now:
            send_time += timedelta(days=1)
        sleep_seconds = (send_time - now).total_seconds()
        print(f"[{datetime.now()}] زمان خواب تا ارسال ترند: {sleep_seconds/60:.1f} دقیقه")
        time.sleep(sleep_seconds)
        send_daily_trends()


if __name__ == "__main__":
    # اجرای دو Thread همزمان: اخبار دوره‌ای + ترند روزانه
    Thread(target=schedule_news, args=(3,), daemon=True).start()  # هر 3 ساعت یک‌بار
    Thread(target=schedule_daily_trends, args=(23,55), daemon=True).start()  # هر روز 23:55

    print("ربات شروع شد. CTRL+C برای خروج")
    while True:
        time.sleep(60)  # حلقه اصلی برای نگه داشتن Thread ها

