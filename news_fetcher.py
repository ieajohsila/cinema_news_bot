"""
ماژول جمع‌آوری اخبار از منابع RSS و Scraping
ذخیره اخبار برای تحلیل ترند روزانه
"""

import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging
from database import get_rss_sources, get_scrape_sources, is_sent, mark_sent, save_collected_news

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fetch_rss_feed(url):
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
        seen_in_page = set()
        for link in links[:30]:
            href = link.get("href", "")
            if href.startswith("/"):
                from urllib.parse import urljoin
                href = urljoin(url, href)
            if not href.startswith("http") or href in seen_in_page or is_sent(href):
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
            seen_in_page.add(href)
            mark_sent(href)
            if len(articles) >= 10:
                break
        logger.info(f"✅ Scrape: {len(articles)} خبر جدید از {url[:30]}")
        return articles
    except Exception as e:
        logger.error(f"❌ خطا در Scraping {url[:50]}: {e}")
        return []


def fetch_all_news():
    logger.info("\n" + "="*60)
    logger.info("🔄 شروع جمع‌آوری اخبار از تمام منابع...")
    all_articles = []
    rss_sources = get_rss_sources()
    logger.info(f"📰 تعداد منابع RSS: {len(rss_sources)}")
    for rss in rss_sources:
        all_articles.extend(fetch_rss_feed(rss))
    scrape_sources = get_scrape_sources()
    logger.info(f"🕷️  تعداد منابع Scraping: {len(scrape_sources)}")
    for scrape in scrape_sources:
        all_articles.extend(fetch_scraped_page(scrape))
    logger.info(f"✅ جمعاً {len(all_articles)} خبر جدید جمع‌آوری شد")
    if all_articles:
        save_collected_news(all_articles)
        logger.info("💾 اخبار در فایل ذخیره شدند")
    return all_articles


if __name__ == "__main__":
    news = fetch_all_news()
    print(f"📊 تعداد اخبار: {len(news)}")
    if news:
        print(f"📰 اولین خبر: {news[0]['title'][:60]}...")
