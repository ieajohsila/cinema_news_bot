# news_fetcher.py

import logging
import feedparser
import httpx
from typing import List, Dict
from default_sources import DEFAULT_RSS_SOURCES, DEFAULT_SCRAPE_SITES

logger = logging.getLogger("news_fetcher")


def is_valid_rss_item(entry) -> bool:
    """
    🔧 FIX: فیلتر کردن آیتم‌های نامعتبر RSS
    """
    title = entry.get("title", "").strip()
    link = entry.get("link", "").strip()
    
    # فیلتر عناوین خالی
    if not title or not link:
        return False
    
    # فیلتر لینک‌های RSS خود منبع
    if "/feed" in link.lower() or "/rss" in link.lower():
        return False
    
    # فیلتر عناوین کوتاه یا بی‌معنی
    if len(title) < 10:
        return False
    
    # فیلتر عناوین که فقط نام سایت هستن
    invalid_titles = [
        'latest news', 'آخرین اخبار', 'home', 'feed',
        'rss', 'cinema', 'movies', 'news', 'homepage'
    ]
    if title.lower() in invalid_titles:
        return False
    
    return True


# =========================
# RSS FETCHER
# =========================
def fetch_rss_news() -> List[Dict]:
    news_list: List[Dict] = []

    logger.info(f"🔄 شروع جمع‌آوری اخبار از منابع RSS ({len(DEFAULT_RSS_SOURCES)})...")

    for url in DEFAULT_RSS_SOURCES:
        try:
            feed = feedparser.parse(url)
            count = 0

            for entry in feed.entries:
                # 🔧 FIX: فیلتر کردن آیتم‌های نامعتبر
                if not is_valid_rss_item(entry):
                    continue
                
                news = {
                    "title": entry.get("title", "").strip(),
                    "link": entry.get("link", "").strip(),
                    "summary": entry.get("summary", "").strip(),
                    "source": url,
                    "type": "rss",
                }

                news_list.append(news)
                count += 1

            logger.info(f"✅ RSS: {count} خبر جدید از {url}")

        except Exception as e:
            logger.error(f"❌ خطا در RSS {url}: {e}")

    return news_list


# =========================
# SCRAPER (SIMPLE & SAFE)
# =========================
def fetch_scrape_news() -> List[Dict]:
    news_list: List[Dict] = []

    logger.info(f"🔄 شروع جمع‌آوری اخبار از منابع Scrape ({len(DEFAULT_SCRAPE_SITES)})...")

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; CinemaNewsBot/1.0)"
    }

    for url in DEFAULT_SCRAPE_SITES:
        try:
            with httpx.Client(headers=headers, follow_redirects=True, timeout=15) as client:
                response = client.get(url)
                response.raise_for_status()

            # 🔧 FIX: چک کردن اینکه لینک RSS نباشد
            if "/feed" in url.lower() or "/rss" in url.lower():
                logger.debug(f"⚠️ Scrape: لینک RSS است، رد شد: {url}")
                continue

            # فعلاً فقط لینک صفحه را ثبت می‌کنیم (safe mode)
            news = {
                "title": f"Latest news from {url.split('/')[2]}",
                "link": url,
                "summary": "",
                "source": url,
                "type": "scrape",
            }

            news_list.append(news)
            logger.info(f"✅ Scrape: 1 آیتم از {url}")

        except Exception as e:
            logger.error(f"❌ خطا در Scraping {url}: {e}")

    return news_list


# =========================
# MAIN API (⚠️ حیاتی)
# =========================
def fetch_all_news() -> List[Dict]:
    """
    ⚠️ این تابع نباید حذف یا rename شود
    Admin Bot و News Scheduler به آن وابسته‌اند
    """

    all_news: List[Dict] = []

    rss_news = fetch_rss_news()
    scrape_news = fetch_scrape_news()

    all_news.extend(rss_news)
    all_news.extend(scrape_news)

    logger.info(f"✅ جمعاً {len(all_news)} خبر جمع‌آوری شد")

    return all_news
