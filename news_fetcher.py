"""
ماژول جمع‌آوری اخبار از منابع RSS و Scraping
و ذخیره روزانه اخبار برای تحلیل ترند
"""

import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import logging
import os
import json

from database import get_rss_sources, get_scrape_sources, is_sent, mark_sent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DAILY_NEWS_DIR = "data/daily_news"
os.makedirs(DAILY_NEWS_DIR, exist_ok=True)


def save_collected_news(all_articles):
    """ذخیره اخبار در فایل روزانه"""
    today_str = datetime.now().strftime("%Y-%m-%d")
    file_path = os.path.join(DAILY_NEWS_DIR, f"{today_str}.json")
    
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(all_articles, f, ensure_ascii=False, indent=2)
        logger.info(f"💾 {len(all_articles)} خبر در {file_path} ذخیره شد")
    except Exception as e:
        logger.error(f"❌ خطا در ذخیره اخبار روزانه: {e}")


def get_collected_news(date_str=None):
    """خواندن اخبار روزانه"""
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")
    file_path = os.path.join(DAILY_NEWS_DIR, f"{date_str}.json")
    
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"❌ خطا در خواندن اخبار روزانه: {e}")
    return []


def fetch_rss_feed(url):
    """دریافت اخبار از یک فید RSS"""
    try:
        logger.info(f"📰 در حال خواندن RSS: {url[:50]}...")
        feed = feedparser.parse(url)
        articles = []
        for entry in feed.entries[:15]:
            link = entry.get("link", "")
            if not link or is_sent(link):
                continue
            published = entry.get("published_parsed") or entry.get("updated_parsed")
            if published:
                try:
                    pub_date = datetime(*published[:6])
                except:
                    pub_date = datetime.now()
            else:
                pub_date = datetime.now()
            if (datetime.now() - pub_date).days > 7:
                continue
            title = entry.get("title", "بدون عنوان")
            summary = entry.get("summary", "") or entry.get("description", "")
            if summary:
                soup = BeautifulSoup(summary, "html.parser")
                summary = soup.get_text().strip()[:400]
            articles.append({
                "title": title,
                "link": link,
                "url": link,
                "summary": summary,
                "source": url,
                "published": pub_date.isoformat(),
            })
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
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        articles = []
        links = soup.find_all("a", href=True)
        seen_in_this_page = set()
        for link in links[:30]:
            href = link.get("href", "")
            if href.startswith("/"):
                from urllib.parse import urljoin
                href = urljoin(url, href)
            if not href.startswith("http"):
                continue
            if href in seen_in_this_page or is_sent(href):
                continue
            keywords = ["news", "article", "cinema", "film", "movie", "entertainment", "/20"]
            if not any(k in href.lower() for k in keywords):
                continue
            title = link.get_text(strip=True)
            if len(title) < 15:
                continue
            title = " ".join(title.split())
            articles.append({
                "title": title,
                "link": href,
                "url": href,
                "summary": "",
                "source": url,
                "published": datetime.now().isoformat(),
            })
            seen_in_this_page.add(href)
            mark_sent(href)
            if len(articles) >= 10:
                break
        logger.info(f"✅ Scrape: {len(articles)} خبر جدید از {url[:30]}")
        return articles
    except Exception as e:
        logger.error(f"❌ خطا در Scraping {url[:50]}: {e}")
        return []


def fetch_all_news():
    """جمع‌آوری تمام اخبار از همه منابع و ذخیره روزانه"""
    logger.info("\n" + "="*60)
    logger.info("🔄 شروع جمع‌آوری اخبار از تمام منابع...")
    logger.info("="*60)
    all_articles = []
    rss_sources = get_rss_sources()
    for rss_url in rss_sources:
        all_articles.extend(fetch_rss_feed(rss_url))
    scrape_sources = get_scrape_sources()
    for scrape_url in scrape_sources:
        all_articles.extend(fetch_scraped_page(scrape_url))
    logger.info(f"✅ جمعاً {len(all_articles)} خبر جدید جمع‌آوری شد")
    if all_articles:
        save_collected_news(all_articles)
    return all_articles


if __name__ == "__main__":
    news = fetch_all_news()
    print(f"📰 تعداد اخبار: {len(news)}")
