# news_fetcher.py

import logging
import feedparser
import httpx
from typing import List, Dict
from default_sources import DEFAULT_RSS_SOURCES, DEFAULT_SCRAPE_SITES

logger = logging.getLogger("news_fetcher")


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
                news = {
                    "title": entry.get("title", "").strip(),
                    "link": entry.get("link", "").strip(),
                    "summary": entry.get("summary", "").strip(),
                    "source": url,
                    "type": "rss",
                }

                # حداقل دیتا
                if news["title"] and news["link"]:
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

            # فعلاً فقط لینک صفحه را ثبت می‌کنیم (safe mode)
            news = {
                "title": f"Latest news from {url}",
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
