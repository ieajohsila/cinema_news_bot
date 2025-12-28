"""
ربات خبری سینما - فایل اصلی
این فایل هم پنل ادمین و هم سرویس خبررسانی خودکار را اجرا می‌کند
"""
import os
import asyncio
import logging
from threading import Thread
from telegram import Bot
from telegram.error import TelegramError

# تنظیم logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def cleanup_bot():
    """
    پاکسازی و آماده‌سازی ربات قبل از شروع
    - حذف webhook
    - حذف pending updates
    - جلوگیری از Conflict
    """
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        logger.error("BOT_TOKEN not found!")
        return False
    
    bot = Bot(token=bot_token)
    
    try:
        # 1. حذف webhook (اگر قبلاً تنظیم شده)
        logger.info("🧹 در حال حذف webhook...")
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("✅ Webhook حذف شد")
        
        # 2. دریافت و پاک کردن pending updates
        logger.info("🧹 در حال پاک کردن pending updates...")
        updates = await bot.get_updates(timeout=2)
        
        if updates:
            # دریافت آخرین update_id
            last_update_id = updates[-1].update_id
            # پاک کردن همه updates تا الان
            await bot.get_updates(offset=last_update_id + 1, timeout=2)
            logger.info(f"✅ {len(updates)} pending update پاک شد")
        else:
            logger.info("✅ هیچ pending update وجود ندارد")
        
        # 3. تست اتصال
        me = await bot.get_me()
        logger.info(f"✅ اتصال موفق: @{me.username}")
        
        return True
        
    except TelegramError as e:
        logger.error(f"❌ خطا در cleanup: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ خطای غیرمنتظره در cleanup: {e}")
        return False


def start_healthcheck_server():
    """
    شروع سرور ساده برای healthcheck
    برای جلوگیری از restart های اضافی در Railway
    """
    try:
        from flask import Flask
        
        app = Flask(__name__)
        
        @app.route('/')
        def home():
            return "🎬 Cinema News Bot is running!"
        
        @app.route('/health')
        def health():
            return {'status': 'healthy', 'service': 'cinema_news_bot'}, 200
        
        # پورت از environment variable
        port = int(os.getenv('PORT', 8080))
        
        logger.info(f"🏥 سرور healthcheck در حال اجرا در پورت {port}")
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
        
    except ImportError:
        logger.warning("⚠️ Flask نصب نیست. Healthcheck غیرفعال است.")
        logger.warning("💡 برای فعال‌سازی: pip install flask")
    except Exception as e:
        logger.error(f"❌ خطا در healthcheck server: {e}")


def main():
    """
    راه‌اندازی اصلی ربات
    """
    print("\n" + "="*70)
    print("🎬 ربات خبری سینما - راه‌اندازی کامل")
    print("="*70)
    
    # بررسی BOT_TOKEN
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        print("❌ خطا: BOT_TOKEN در Environment Variables تنظیم نشده است!")
        print("💡 راهنما: export BOT_TOKEN='YOUR_TOKEN_HERE'")
        return
    
    print("✅ BOT_TOKEN یافت شد")
    
    # بررسی GEMINI_API_KEY
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        print("⚠️  هشدار: GEMINI_API_KEY تنظیم نشده - ترجمه غیرفعال است")
        print("💡 راهنما: export GEMINI_API_KEY='YOUR_KEY_HERE'")
    else:
        print("✅ GEMINI_API_KEY یافت شد")
    
    print("\n🧹 پاکسازی و آماده‌سازی...")
    print("="*70)
    
    # پاکسازی قبل از شروع (برای جلوگیری از Conflict)
    cleanup_success = asyncio.run(cleanup_bot())
    
    if not cleanup_success:
        print("⚠️  پاکسازی با مشکل مواجه شد، ولی ادامه می‌دهیم...")
    
    print("\n" + "="*70)
    print("📋 سرویس‌های در حال اجرا:")
    print("  1️⃣  پنل مدیریت ادمین (admin_bot)")
    print("  2️⃣  سرویس خبررسانی خودکار (news_scheduler)")
    print("  3️⃣  سرور healthcheck (port 8080)")
    print("\n🛑 برای توقف: CTRL+C")
    print("="*70 + "\n")
    
    # شروع healthcheck server در background
    healthcheck_thread = Thread(target=start_healthcheck_server, daemon=True)
    healthcheck_thread.start()
    
    # اجرای news_scheduler در Thread جداگانه
    try:
        from news_scheduler import start_scheduler
        scheduler_thread = Thread(target=start_scheduler, daemon=True)
        scheduler_thread.start()
        logger.info("✅ News scheduler شروع شد")
    except ImportError as e:
        logger.error(f"❌ خطا در import news_scheduler: {e}")
    except Exception as e:
        logger.error(f"❌ خطا در شروع news_scheduler: {e}")
    
    # اجرای admin_bot در Thread اصلی
    try:
        print("🤖 راه‌اندازی پنل ادمین...\n")
        from admin_bot import app as admin_app
        
        # اجرای ربات با مدیریت خطا
        admin_app.run_polling(
            drop_pending_updates=True,  # نادیده گرفتن پیام‌های قدیمی
            allowed_updates=['message', 'callback_query']  # فقط این نوع update ها
        )
        
    except ImportError as e:
        logger.error(f"❌ خطا در import admin_bot: {e}")
    except Exception as e:
        logger.error(f"❌ خطا در اجرای admin_bot: {e}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 ربات متوقف شد. خداحافظ!")
    except Exception as e:
        logger.error(f"\n❌ خطای غیرمنتظره: {e}", exc_info=True)
        print(f"\n❌ خطای غیرمنتظره: {e}")
