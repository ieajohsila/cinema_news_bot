"""
اسکریپت مقداردهی اولیه
این فایل منابع پیش‌فرض را به database اضافه می‌کند
"""

from database import add_rss_source, add_scrape_source, get_rss_sources, get_scrape_sources
from default_sources import DEFAULT_RSS_SOURCES, DEFAULT_SCRAPE_SITES

def initialize_sources():
    """افزودن منابع پیش‌فرض به database"""
    print("\n" + "="*60)
    print("🔧 مقداردهی اولیه منابع...")
    print("="*60 + "\n")
    
    # بررسی منابع فعلی
    current_rss = get_rss_sources()
    current_scrape = get_scrape_sources()
    
    print(f"📊 وضعیت فعلی:")
    print(f"   RSS: {len(current_rss)} منبع")
    print(f"   Scrape: {len(current_scrape)} منبع\n")
    
    # افزودن RSS
    added_rss = 0
    for url in DEFAULT_RSS_SOURCES:
        if url not in current_rss:
            add_rss_source(url)
            added_rss += 1
            print(f"✅ RSS اضافه شد: {url}")
    
    # افزودن Scrape
    added_scrape = 0
    for url in DEFAULT_SCRAPE_SITES:
        if url not in current_scrape:
            add_scrape_source(url)
            added_scrape += 1
            print(f"✅ Scrape اضافه شد: {url}")
    
    print("\n" + "="*60)
    print(f"✅ مقداردهی کامل شد!")
    print(f"   📰 {added_rss} RSS جدید اضافه شد")
    print(f"   🕷️  {added_scrape} Scrape جدید اضافه شد")
    print("="*60 + "\n")


if __name__ == "__main__":
    initialize_sources()
