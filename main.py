"""
🎬 ربات خبری سینما - نسخه بهینه شده
Admin Bot در thread جداگانه، News Scheduler در async loop
"""

import os
import asyncio
import logging
from threading import Thread
import time

from telegram import Bot
from telegram.error import TelegramError

# ==============================
# Logging
# ==============================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==============================
# Cleanup Bot
# ==============================
async def cleanup_bot():
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        logger.error("❌ BOT_TOKEN پیدا نشد!")
        return False

    bot = Bot(token=bot_token)

    try:
        logger.info("🧹 حذف webhook...")
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("✅ Webhook حذف شد")

        me = await bot.get_me()
        logger.info(f"✅ اتصال موفق: @{me.username}")
        return True

    except Exception as e:
        logger.error(f"❌ خطا در cleanup: {e}")
        return False

# ==============================
# Healthcheck Server
# ==============================
def start_healthcheck_server():
    try:
        from flask import Flask, jsonify

        app = Flask(__name__)

        @app.route('/')
        def home():
            return "🎬 Cinema News Bot is running!"

        @app.route('/health')
        def health():
            return jsonify({'status': 'healthy', 'service': 'cinema_news_bot'}), 200

        port = int(os.getenv('PORT', '8080'))
        logger.info(f"🏥 Healthcheck server running on port {port}")
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

    except ImportError:
        logger.warning("⚠️ Flask نصب نیست. Healthcheck غیرفعال شد.")
    except Exception as e:
        logger.error(f"❌ خطا در healthcheck: {e}")

# ==============================
# اجرا کننده scheduler
# ==============================
async def start_news_scheduler():
    try:
        from news_scheduler import run_scheduler
        logger.info("📰 شروع News Scheduler...")
        await run_scheduler()
    except ImportError as e:
        logger.error(f"❌ news_scheduler پیدا نشد: {e}")
    except Exception as e:
        logger.error(f"❌ خطا در اجرای news_scheduler: {e}")
        import traceback
        logger.error(traceback.format_exc())

# ==============================
# اجرا کننده admin_bot (Thread)
# ==============================
def start_admin_bot_thread():
    """اجرای Admin Bot در thread جداگانه"""
    try:
        # صبر کوتاه تا سیستم آماده شود
        time.sleep(2)
        
        logger.info("🤖 شروع Admin Bot...")
        from admin_bot import app as admin_app
        
        # اجرای مستقیم polling (blocking)
        admin_app.run_polling(
            drop_pending_updates=True,
            allowed_updates=['message', 'callback_query']
        )
        
    except ImportError as e:
        logger.error(f"❌ admin_bot پیدا نشد: {e}")
    except Exception as e:
        logger.error(f"❌ خطا در اجرای admin_bot: {e}")
        import traceback
        logger.error(traceback.format_exc())

# ==============================
# Main Async
# ==============================
async def main_async():
    print("\n" + "="*70)
    print("🎬 ربات خبری سینما - راه‌اندازی کامل")
    print("="*70)

    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN تنظیم نشده است!")
        return
    print("✅ BOT_TOKEN یافت شد")

    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        print("⚠️ GEMINI_API_KEY تنظیم نشده - ترجمه غیرفعال است")
    else:
        print("✅ GEMINI_API_KEY یافت شد")
    
    TARGET_CHAT_ID = os.getenv("TARGET_CHAT_ID")
    if TARGET_CHAT_ID:
        print(f"✅ TARGET_CHAT_ID یافت شد: {TARGET_CHAT_ID}")
    else:
        print("⚠️ TARGET_CHAT_ID تنظیم نشده - از پنل ادمین تنظیم کنید")

    print("\n🧹 پاکسازی و آماده‌سازی ربات...")
    cleanup_success = await cleanup_bot()
    if not cleanup_success:
        print("⚠️ پاکسازی کامل نبود، ادامه می‌دهیم...")

    print("\n📋 سرویس‌های فعال:")
    print("  1️⃣ Admin Bot (Thread)")
    print("  2️⃣ News Scheduler (Async)")
    print("  3️⃣ Healthcheck Server (8080)")
    print("\n🛑 خروج: CTRL+C\n")

    # Healthcheck server
    Thread(target=start_healthcheck_server, daemon=True, name="HealthCheck").start()
    
    # Admin Bot
    admin_thread = Thread(target=start_admin_bot_thread, daemon=True, name="AdminBot")
    admin_thread.start()
    logger.info("✅ Admin Bot thread started")
    
    # صبر کوتاه تا Admin Bot شروع شود
    await asyncio.sleep(3)

    # News Scheduler در main loop
    try:
        await start_news_scheduler()
    except Exception as e:
        logger.error(f"❌ خطا در اجرای سرویس‌ها: {e}", exc_info=True)

# ==============================
# Entry Point
# ==============================
def main():
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("\n\n👋 ربات متوقف شد. خداحافظ!")
    except Exception as e:
        logger.error("❌ خطای غیرمنتظره", exc_info=True)
        print(f"\n❌ خطای غیرمنتظره: {e}")

if __name__ == "__main__":
    main()
