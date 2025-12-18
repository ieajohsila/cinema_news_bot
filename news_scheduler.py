import os
import feedparser
from telegram import Bot
from datetime import date, datetime, timedelta
import time
from threading import Thread
from scrapers import extract_article
from translation import translate_title
from importance import classify_importance
from category import classify_category
from database import is_sent, mark_sent, get_setting, get_rss_sources, get_scrape_sources
from trends import save_topic, daily_trends, normalize

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(BOT_TOKEN)


def send_news(chat_id, title, summary, image, d, site, link):
    """ارسال یک خبر به کانال/گروه"""
    try:
        category = classify_category(title, summary)
        importance = classify_importance(title, summary)
        min_level = int(get_setting("min_importance", 1))
        
        if importance < min_level:
            print(f"⏭️  خبر فیلتر شد (اهمیت {importance} < {min_level})")
            return
        
        # ترجمه عنوان
        title_fa = translate_title(title)
        summary_fa = translate_title(summary[:300])  # محدود کردن طول خلاصه
        
        # ساخت کپشن
        caption = (
            f"{category}\n\n"
            f"*{title_fa}*\n\n"
            f"{summary_fa}\n\n"
            f"📅 {d}\n"
            f"🌐 {site}\n\n"
            f"🔗 [خبر اصلی]({link})"
        )
        
        # ارسال
        if image:
            bot.send_photo(chat_id=chat_id, photo=image, caption=caption, parse_mode="Markdown")
        else:
            bot.send_message(chat_id=chat_id, text=caption, parse_mode="Markdown")
        
        mark_sent(link)
        save_topic(normalize(title), site, d)
        print(f"✅ خبر ارسال شد: {title[:50]}...")
        
    except Exception as e:
        print(f"❌ خطا در ارسال خبر: {e}")


def fetch_rss_and_send(chat_id):
    """دریافت اخبار از منابع RSS"""
    rss_sources = get_rss_sources()
    
    if not rss_sources:
        print("⚠️  هیچ منبع RSS تعریف نشده است.")
        return
    
    print(f"📰 در حال بررسی {len(rss_sources)} منبع RSS...")
    
    for url in rss_sources:
        try:
            feed = feedparser.parse(url)
            print(f"🔍 بررسی: {url} ({len(feed.entries)} خبر)")
            
            for entry in feed.entries[:5]:  # فقط 5 خبر اول
                link = entry.get('link', '')
                
                if is_sent(link):
                    continue
                
                try:
                    title, summary, image, d, site = extract_article(link)
                    send_news(chat_id, title, summary, image, d, site, link)
                    time.sleep(2)  # تاخیر برای جلوگیری از flood
                    
                except Exception as e:
                    print(f"⚠️  خطا در پردازش {link}: {e}")
                    
        except Exception as e:
            print(f"❌ خطا در خواندن RSS {url}: {e}")


def fetch_scrape_and_send(chat_id):
    """دریافت اخبار از منابع Scraping"""
    scrape_sources = get_scrape_sources()
    
    if not scrape_sources:
        print("⚠️  هیچ منبع Scraping تعریف نشده است.")
        return
    
    print(f"🕷️  در حال بررسی {len(scrape_sources)} منبع Scraping...")
    
    for url in scrape_sources:
        try:
            if is_sent(url):
                continue
            
            title, summary, image, d, site = extract_article(url)
            send_news(chat_id, title, summary, image, d, site, url)
            time.sleep(2)
            
        except Exception as e:
            print(f"❌ خطا در Scraping {url}: {e}")


def send_daily_trends():
    """ارسال ترندهای روزانه"""
    chat_id = get_setting("TARGET_CHAT_ID")
    
    if not chat_id:
        print("⚠️  آیدی مقصد تنظیم نشده است.")
        return
    
    today = date.today().isoformat()
    trends = daily_trends(today)
    
    if not trends:
        print("ℹ️  ترندی برای امروز یافت نشد.")
        return
    
    msg = "📊 *ترندهای امروز سینما*\n\n"
    for topic, count in trends[:10]:  # فقط 10 ترند اول
        msg += f"🔥 {topic} ({count} منبع)\n"
    
    try:
        bot.send_message(chat_id=int(chat_id), text=msg, parse_mode="Markdown")
        print("✅ ترندهای روزانه ارسال شد.")
    except Exception as e:
        print(f"❌ خطا در ارسال ترندها: {e}")


def schedule_news(interval_hours=3):
    """اجرای دوره‌ای اخبار"""
    while True:
        print(f"\n{'='*60}")
        print(f"⏰ [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] شروع جمع‌آوری اخبار")
        print(f"{'='*60}\n")
        
        chat_id = get_setting("TARGET_CHAT_ID")
        
        if not chat_id:
            print("⚠️  آیدی مقصد تنظیم نشده است. لطفاً از پنل ادمین تنظیم کنید.")
        else:
            fetch_rss_and_send(chat_id)
            fetch_scrape_and_send(chat_id)
        
        print(f"\n{'='*60}")
        print(f"✅ پایان ارسال اخبار. خواب به مدت {interval_hours} ساعت...")
        print(f"{'='*60}\n")
        
        time.sleep(interval_hours * 3600)


def schedule_daily_trends(hour=23, minute=55):
    """ارسال ترند روزانه در ساعت مشخص"""
    while True:
        now = datetime.now()
        send_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        if send_time < now:
            send_time += timedelta(days=1)
        
        sleep_seconds = (send_time - now).total_seconds()
        
        print(f"⏰ زمان باقی‌مانده تا ارسال ترند: {sleep_seconds/3600:.1f} ساعت")
        time.sleep(sleep_seconds)
        
        send_daily_trends()


def start_scheduler():
    """شروع scheduler"""
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN تنظیم نشده است!")
        return
    
    print("\n" + "="*60)
    print("🤖 سرویس خبررسانی خودکار سینما")
    print("="*60)
    print(f"⏰ دریافت اخبار: هر 3 ساعت")
    print(f"📊 ارسال ترندها: روزانه ساعت 23:55")
    print(f"🛑 برای توقف: CTRL+C")
    print("="*60 + "\n")
    
    # اجرای دو Thread همزمان
    Thread(target=schedule_news, args=(3,), daemon=True).start()
    Thread(target=schedule_daily_trends, args=(23, 55), daemon=True).start()
    
    # نگه داشتن برنامه
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n\n👋 سرویس متوقف شد.")


if __name__ == "__main__":
    start_scheduler()
