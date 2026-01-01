"""
ماژول جمع‌آوری اخبار از منابع RSS و Scraping
"""

import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import logging

from database import get_rss_sources, get_scrape_sources, is_sent, mark_sent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fetch_rss_feed(url):
    """دریافت اخبار از یک فید RSS"""
    try:
        logger.info(f"📰 در حال خواندن RSS: {url[:50]}...")
        feed = feedparser.parse(url)
        articles = []
        
        for entry in feed.entries[:15]:  # فقط 15 خبر آخر
            link = entry.get("link", "")
            
            # چک کردن اینکه قبلاً دیده شده یا نه
            if not link or is_sent(link):
                continue
            
            # استخراج تاریخ
            published = entry.get("published_parsed") or entry.get("updated_parsed")
            if published:
                try:
                    pub_date = datetime(*published[:6])
                except:
                    pub_date = datetime.now()
            else:
                pub_date = datetime.now()
            
            # فقط اخبار 7 روز اخیر
            if (datetime.now() - pub_date).days > 7:
                continue
            
            title = entry.get("title", "بدون عنوان")
            summary = entry.get("summary", "") or entry.get("description", "")
            
            # پاک‌سازی HTML از summary
            if summary:
                soup = BeautifulSoup(summary, "html.parser")
                summary = soup.get_text().strip()[:400]
            
            articles.append({
                "title": title,
                "link": link,
                "summary": summary,
                "source": url,
                "published": pub_date.isoformat(),
            })
            
            # علامت‌گذاری به عنوان دیده شده
            mark_sent(link)
        
        logger.info(f"✅ RSS: {len(articles)} خبر جدید از {url[:30]}")
        return articles
        
    except Exception as e:
        logger.error(f"❌ خطا در RSS {url[:50]}: {e}")
        return []


def fetch_scraped_page(url):
    """دریافت اخبار با scraping مستقیم از صفحه"""
    try:
        logger.info(f"🕷️  در حال Scraping: {url[:50]}...")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, "html.parser")
        articles = []
        
        # استراتژی عمومی: پیدا کردن لینک‌های خبری
        links = soup.find_all("a", href=True)
        
        seen_in_this_page = set()
        
        for link in links[:30]:  # محدود به 30 لینک
            href = link.get("href", "")
            
            # اگر لینک نسبی است، کامل کنید
            if href.startswith("/"):
                from urllib.parse import urljoin
                href = urljoin(url, href)
            
            # چک کردن که لینک معتبر باشه
            if not href.startswith("http"):
                continue
            
            # جلوگیری از تکرار در همین صفحه
            if href in seen_in_this_page:
                continue
            
            # چک کردن تکراری بودن در دیتابیس
            if is_sent(href):
                continue
            
            # فقط لینک‌های مرتبط با خبر
            keywords = ["news", "article", "cinema", "film", "movie", "entertainment", "/20"]
            if not any(keyword in href.lower() for keyword in keywords):
                continue
            
            title = link.get_text(strip=True)
            if len(title) < 15:  # عنوان خیلی کوتاه
                continue
            
            # حذف کاراکترهای اضافی
            title = " ".join(title.split())
            
            articles.append({
                "title": title,
                "link": href,
                "summary": "",
                "source": url,
                "published": datetime.now().isoformat(),
            })
            
            seen_in_this_page.add(href)
            mark_sent(href)
            
            # محدودیت تعداد اخبار از هر صفحه
            if len(articles) >= 10:
                break
        
        logger.info(f"✅ Scrape: {len(articles)} خبر جدید از {url[:30]}")
        return articles
        
    except requests.exceptions.Timeout:
        logger.error(f"⏱️  Timeout در Scraping {url[:50]}")
        return []
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ خطای شبکه در Scraping {url[:50]}: {e}")
        return []
    except Exception as e:
        logger.error(f"❌ خطای غیرمنتظره در Scraping {url[:50]}: {e}")
        return []


def fetch_all_news():
    """جمع‌آوری تمام اخبار از همه منابع"""
    logger.info("\n" + "="*60)
    logger.info("🔄 شروع جمع‌آوری اخبار از تمام منابع...")
    logger.info("="*60)
    
    all_articles = []
    
    # دریافت از RSS
    rss_sources = get_rss_sources()
    logger.info(f"📰 تعداد منابع RSS: {len(rss_sources)}")
    for rss_url in rss_sources:
        articles = fetch_rss_feed(rss_url)
        all_articles.extend(articles)
    
    # دریافت از Scraping
    scrape_sources = get_scrape_sources()
    logger.info(f"🕷️  تعداد منابع Scraping: {len(scrape_sources)}")
    for scrape_url in scrape_sources:
        articles = fetch_scraped_page(scrape_url)
        all_articles.extend(articles)
    
    logger.info("="*60)
    logger.info(f"✅ جمعاً {len(all_articles)} خبر جدید جمع‌آوری شد")
    logger.info("="*60 + "\n")
    
    return all_articles


if __name__ == "__main__":
    # تست
    print("🧪 تست ماژول news_fetcher...\n")
    news = fetch_all_news()
    print(f"\n📊 تعداد اخبار: {len(news)}")
    if news:
        print(f"📰 اولین خبر: {news[0]['title'][:60]}...")
