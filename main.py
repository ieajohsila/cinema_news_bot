"""
ربات خبری سینما - فایل اصلی
این فایل هم پنل ادمین و هم سرویس خبررسانی خودکار را اجرا می‌کند
"""

import os
from threading import Thread
from admin_bot import app as admin_app
from news_scheduler import start_scheduler

def main():
    print("\n" + "="*70)
    print("🎬 ربات خبری سینما - راه‌اندازی کامل")
    print("="*70)
    
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        print("❌ خطا: BOT_TOKEN در Environment Variables تنظیم نشده است!")
        print("💡 راهنما: export BOT_TOKEN='YOUR_TOKEN_HERE'")
        return
    
    print("✅ BOT_TOKEN یافت شد")
    print("\n📋 سرویس‌های در حال اجرا:")
    print("  1️⃣  پنل مدیریت ادمین (admin_bot)")
    print("  2️⃣  سرویس خبررسانی خودکار (news_scheduler)")
    print("\n🛑 برای توقف: CTRL+C")
    print("="*70 + "\n")
    
    # اجرای news_scheduler در Thread جداگانه
    scheduler_thread = Thread(target=start_scheduler, daemon=True)
    scheduler_thread.start()
    
    # اجرای admin_bot در Thread اصلی
    print("🤖 راه‌اندازی پنل ادمین...\n")
    admin_app.run_polling()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 ربات متوقف شد. خداحافظ!")
    except Exception as e:
        print(f"\n❌ خطای غیرمنتظره: {e}")
