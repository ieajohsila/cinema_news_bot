import logging
from bs4 import BeautifulSoup
import httpx
import feedparser
from default_sources import DEFAULT_RSS_SOURCES, DEFAULT_SCRAPE_SITES

logger = logging.getLogger("news_fetcher")
logging.basicConfig(level=logging.INFO)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}

def fetch_rss_news(url):
    """جمع‌آوری اخبار از RSS"""
    try:
        feed = feedparser.parse(url)
        news_items = []
        for entry in feed.entries:
            link = entry.get('link')
            title = entry.get('title', 'بدون عنوان')
            summary = entry.get('summary', '')
            if link:
                news_items.append({"title": title, "link": link, "summary": summary})
            else:
                logger.warning(f"خبر ناقص در RSS: {title}")
        logger.info(f"✅ RSS: {len(news_items)} خبر جدید از {url}")
        return news_items
    except Exception as e:
        logger.error(f"❌ خطا در RSS {url}: {e}")
        return []

def scrape_news(url):
    """جمع‌آوری اخبار از سایت‌ها با Scraping"""
    try:
        with httpx.Client(headers=HEADERS, follow_redirects=True, timeout=15) as client:
            response = client.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            news_items = []

            # استخراج لینک‌ها و عنوان‌ها از تگ <a> با href کامل
            for a_tag in soup.find_all('a', href=True):
                link = a_tag['href']
                if not link.startswith("http"):
                    continue  # لینک ناقص رد می‌شود
                title = a_tag.get_text(strip=True) or "خبر بدون عنوان"
                news_items.append({"title": title, "link": link})

            logger.info(f"✅ Scrape: {len(news_items)} خبر جدید از {url}")
            return news_items

    except httpx.HTTPStatusError as e:
        logger.error(f"❌ خطا در Scraping {url}: {e.response.status_code} {e.response.reason_phrase}")
        return []
    except httpx.RequestError as e:
        logger.error(f"❌ خطا در Scraping {url}: {e}")
        return []
    except Exception as e:
        logger.error(f"❌ خطا در Scraping {url}: {e}")
        return []

def collect_all_news():
    """جمع‌آوری تمام اخبار از RSS و Scrape"""
    all_news = []

    logger.info(f"🔄 شروع جمع‌آوری اخبار از منابع RSS ({len(DEFAULT_RSS_SOURCES)})...")
    for rss in DEFAULT_RSS_SOURCES:
        all_news.extend(fetch_rss_news(rss))

    logger.info(f"🔄 شروع جمع‌آوری اخبار از منابع Scrape ({len(DEFAULT_SCRAPE_SITES)})...")
    for site in DEFAULT_SCRAPE_SITES:
        all_news.extend(scrape_news(site))

    logger.info(f"✅ جمعاً {len(all_news)} خبر جدید جمع‌آوری شد")
    return all_news

if __name__ == "__main__":
    news = collect_all_news()
    # برای تست، 5 خبر اول را چاپ می‌کنیم
    for n in news[:5]:
        print(n["title"], n["link"])
