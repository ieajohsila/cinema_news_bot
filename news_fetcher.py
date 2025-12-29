"""
ماژول جمع‌آوری اخبار از منابع RSS و Scraping
ذخیره اخبار برای تحلیل ترند روزانه
"""
"""news_fetcher.py
جمع‌آوری اخبار سینما از RSS و Scrape
"""
import logging
from typing import List, Dict
import feedparser
import httpx
from bs4 import BeautifulSoup

from default_sources import DEFAULT_RSS_SOURCES, DEFAULT_SCRAPE_SITES

logger = logging.getLogger(__name__)


def fetch_rss(url: str) -> List[Dict]:
    """
    جمع‌آوری اخبار از RSS
    """
    articles: List[Dict] = []
    try:
        feed = feedparser.parse(url)
        entries = getattr(feed, 'entries', [])
        if not isinstance(entries, list):
            logger.error(f"❌ RSS {url} نامعتبر است یا entries لیست نیست")
            return []

        for entry in entries:
            article = {
                'title': entry.get('title', '').strip(),
                'url': entry.get('link', '').strip(),
                'published': entry.get('published', ''),
                'source': url
            }
            articles.append(article)

        logger.info(f"✅ RSS: {len(articles)} خبر جدید از {url}")
    except Exception as e:
        logger.error(f"❌ خطا در RSS {url}: {e}")
    return articles


def fetch_scrape(url: str) -> List[Dict]:
    """
    جمع‌آوری اخبار با Scrape
    """
    articles: List[Dict] = []
    try:
        response = httpx.get(url, timeout=15.0)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # پیدا کردن لینک و عنوان اخبار (الگوی ساده)
        for a in soup.find_all('a', href=True):
            title = a.get_text(strip=True)
            link = a['href']

            # فیلتر لینک‌های خالی یا تبلیغ
            if not title or not link or link.startswith('#'):
                continue

            # کامل کردن لینک‌های نسبی
            if link.startswith('/'):
                base = url.rstrip('/')
                link = f"{base}{link}"

            articles.append({
                'title': title,
                'url': link,
                'published': '',
                'source': url
            })

        logger.info(f"✅ Scrape: {len(articles)} خبر جدید از {url}")
    except Exception as e:
        logger.error(f"❌ خطا در Scraping {url}: {e}")
    return articles


def fetch_all_news() -> List[Dict]:
    """
    جمع‌آوری اخبار از همه منابع RSS و Scrape
    """
    all_articles: List[Dict] = []

    logger.info(f"🔄 شروع جمع‌آوری اخبار از منابع RSS ({len(DEFAULT_RSS_SOURCES)})...")
    for url in DEFAULT_RSS_SOURCES:
        articles = fetch_rss(url)
        if not isinstance(articles, list):
            articles = []
        all_articles.extend(articles)

    logger.info(f"🔄 شروع جمع‌آوری اخبار از منابع Scrape ({len(DEFAULT_SCRAPE_SITES)})...")
    for url in DEFAULT_SCRAPE_SITES:
        articles = fetch_scrape(url)
        if not isinstance(articles, list):
            articles = []
        all_articles.extend(articles)

    logger.info(f"✅ جمعاً {len(all_articles)} خبر جدید جمع‌آوری شد")
    return all_articles


# تست مستقیم
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    news = fetch_all_news()
    for i, item in enumerate(news[:5], 1):
        print(f"{i}. {item['title']} ({item['source']})")
