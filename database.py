#!/usr/bin/env python3
"""
اسکریپت تمیزکاری و اصلاح فایل‌های دیتابیس

این اسکریپت:
1. فایل‌های خالی را پر می‌کند
2. فرمت‌های اشتباه را اصلاح می‌کند
3. ساختار صحیح را برمی‌گرداند
"""

import json
import os
from pathlib import Path

DATA_DIR = "data"

# ساختارهای صحیح پیش‌فرض
DEFAULTS = {
    "settings.json": {},
    "sources.json": {"rss": [], "scrape": []},
    "sent.json": [],
    "topics.json": [],
    "collected_news.json": {}
}


def ensure_dir():
    """ساخت پوشه data"""
    os.makedirs(DATA_DIR, exist_ok=True)
    print(f"✅ پوشه {DATA_DIR} آماده است")


def fix_file(filename, default_content):
    """اصلاح یک فایل JSON"""
    filepath = os.path.join(DATA_DIR, filename)
    
    try:
        # بررسی وجود فایل
        if not os.path.exists(filepath):
            print(f"⚠️  {filename} وجود ندارد - ساخت جدید...")
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(default_content, f, ensure_ascii=False, indent=2)
            print(f"✅ {filename} ساخته شد")
            return
        
        # خواندن محتوا
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        # اگر خالی است
        if not content:
            print(f"⚠️  {filename} خالی است - پر کردن...")
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(default_content, f, ensure_ascii=False, indent=2)
            print(f"✅ {filename} پر شد")
            return
        
        # اگر فرمت نادرست است
        try:
            data = json.loads(content)
            
            # بررسی نوع صحیح
            if filename == "sources.json":
                if not isinstance(data, dict) or "rss" not in data or "scrape" not in data:
                    print(f"⚠️  {filename} فرمت اشتباه - اصلاح...")
                    data = default_content
            elif filename == "sent.json":
                if not isinstance(data, list):
                    print(f"⚠️  {filename} باید لیست باشد - اصلاح...")
                    data = default_content
            elif filename == "topics.json":
                if not isinstance(data, list):
                    print(f"⚠️  {filename} باید لیست باشد - اصلاح...")
                    data = default_content
            elif filename == "collected_news.json":
                if not isinstance(data, dict):
                    print(f"⚠️  {filename} باید دیکشنری باشد - اصلاح...")
                    data = default_content
            
            # ذخیره مجدد با فرمت صحیح
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ {filename} فرمت صحیح است")
            
        except json.JSONDecodeError:
            print(f"❌ {filename} JSON نامعتبر - بازنویسی...")
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(default_content, f, ensure_ascii=False, indent=2)
            print(f"✅ {filename} بازنویسی شد")
    
    except Exception as e:
        print(f"❌ خطا در {filename}: {e}")


def show_status():
    """نمایش وضعیت فایل‌ها"""
    print("\n" + "="*60)
    print("📊 وضعیت فایل‌های دیتابیس:")
    print("="*60)
    
    for filename in DEFAULTS.keys():
        filepath = os.path.join(DATA_DIR, filename)
        
        if not os.path.exists(filepath):
            print(f"❌ {filename}: وجود ندارد")
            continue
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            if not content:
                print(f"⚠️  {filename}: خالی")
                continue
            
            data = json.loads(content)
            
            if filename == "sources.json":
                rss_count = len(data.get("rss", []))
                scrape_count = len(data.get("scrape", []))
                print(f"✅ {filename}: {rss_count} RSS, {scrape_count} Scraping")
            
            elif filename == "sent.json":
                count = len(data) if isinstance(data, list) else 0
                print(f"✅ {filename}: {count} خبر ارسال شده")
            
            elif filename == "topics.json":
                count = len(data) if isinstance(data, list) else 0
                print(f"✅ {filename}: {count} topic")
            
            elif filename == "collected_news.json":
                total = sum(len(v) for v in data.values()) if isinstance(data, dict) else 0
                print(f"✅ {filename}: {total} خبر در {len(data)} روز")
            
            elif filename == "settings.json":
                print(f"✅ {filename}: {len(data)} تنظیم")
        
        except Exception as e:
            print(f"❌ {filename}: خطا - {str(e)[:30]}")
    
    print("="*60 + "\n")


def main():
    print("\n" + "="*60)
    print("🔧 اسکریپت اصلاح فایل‌های دیتابیس")
    print("="*60 + "\n")
    
    # ساخت پوشه
    ensure_dir()
    
    # اصلاح تمام فایل‌ها
    print("\n🔄 در حال اصلاح فایل‌ها...\n")
    for filename, default in DEFAULTS.items():
        fix_file(filename, default)
    
    # نمایش وضعیت نهایی
    show_status()
    
    print("✅ اصلاح کامل شد!")
    print("\n💡 اکنون می‌توانید ربات را اجرا کنید:")
    print("   python main.py\n")


if __name__ == "__main__":
    main()
