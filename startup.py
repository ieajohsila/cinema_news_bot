"""
اسکریپت راه‌اندازی ربات
1. مقداردهی اولیه منابع (در صورت نیاز)
2. اجرای ربات
"""

import os
from database import get_rss_sources, get_scrape_sources, add_rss_source, add_scrape_source
from default_sources import DEFAULT_RSS_SOURCES, DEFAULT_SCRAPE_SITES

def initialize_if_needed():
    """اگر منابع خالی باشد، منابع پیش‌فرض را اضافه می‌کند"""
    
    print("\n" + "="*70)
    print("🔍 بررسی منابع...")
    print("="*70)
    
    current_rss = get_rss_sources()
    current_scrape = get_scrape_sources()
    
    print(f"📊 وضعیت فعلی:")
    print(f"   📰 RSS: {len(current_rss)} منبع")
    print(f"   🕷️  Scrape: {len(current_scrape)} منبع")
    
    # اگر هیچ منبعی نداریم، منابع پیش‌فرض رو اضافه کن
    if len(current_rss) == 0 and len(current_scrape) == 0:
        print("\n⚠️  هیچ منبعی یافت نشد. در حال افزودن منابع پیش‌فرض...")
        
        # افزودن RSS
        added_rss = 0
        for url in DEFAULT_RSS_SOURCES:
            try:
                add_rss_source(url)
                added_rss += 1
                print(f"   ✅ RSS: {url[:50]}...")
            except Exception as e:
                print(f"   ⚠️  خطا در افزودن {url}: {e}")
        
        # افزودن Scrape
        added_scrape = 0
        for url in DEFAULT_SCRAPE_SITES:
            try:
                add_scrape_source(url)
                added_scrape += 1
                print(f"   ✅ Scrape: {url[:50]}...")
            except Exception as e:
                print(f"   ⚠️  خطا در افزودن {url}: {e}")
        
        print(f"\n✅ مقداردهی کامل شد!")
        print(f"   📰 {added_rss} منبع RSS اضافه شد")
        print(f"   🕷️  {added_scrape} منبع Scrape اضافه شد")
    else:
        print("\n✅ منابع قبلاً تنظیم شده‌اند.")
    
    print("="*70 + "\n")


if __name__ == "__main__":
    # مقداردهی اولیه
    initialize_if_needed()
    
    # اجرای ربات
    print("🚀 در حال راه‌اندازی ربات...\n")
    
    # Import و اجرای main
    from main import main
    main()
