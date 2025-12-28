"""
ربات خبری سینما - فایل اصلی (اصلاح شده)
این نسخه همه قابلیت‌های قبلی را حفظ می‌کند
و مشکلات event loop / async و ImportError حل شده‌اند
"""

import os
import asyncio
import logging
from threading import Thread
from telegram import Bot
from telegram.error import TelegramError

# ==============================
# تنظیم logging
# ==============================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==============================
# Cleanup Bot قبل از شروع
# ==============================
async def cleanup_bot():
    """
    پاکسازی و آماده‌سازی ربات قبل از شروع:
    - حذف webhook
    - حذف pending updates
    - تست اتصال
    """
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        logger.error("BOT_TOKEN not found!")
        return False

    bot = Bot(token=bot_token)

    try:
        logger.info("🧹 در حال حذف webhook...")
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("✅ Webhook حذف شد")

        logger.info("🧹 در حال پاک کردن pending updates...")
        updates = await bot.get_updates(timeout=2)
        if updates:
            last_update_id = updates[-1].update_id
            await bot.get_updates(offset=last_update_id + 1, timeout=2)
            logger.info(f"✅ {len(updates)} pending update پاک شد")
        else:
            logger.info("✅ هیچ pending update وجود ندارد")

        me = await bot.get_me()
        logger.info(f"✅ اتصال موفق: @{me.username}")
        return True

    except TelegramError as e:
        logger.error(f"❌ خطا در cleanup: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ خطای غیرمنتظره در cleanup: {e}")
        return False


# ==============================
# Healthcheck Server
# ==============================
def start_healthcheck_server():
    """
    سرور ساده Flask برای healthcheck
    """
    try:
        from flask import Flask, jsonify

        app = Flask(__name__)

        @app.route('/')
        def home():
            return "🎬 Cinema News Bot is running!"

        @app.route('/health')
        def health():
            return jsonify({
                'status': 'healthy',
                'service': 'cinema_news_bot'
            }), 200

        port = int(os.getenv('PORT', 8080))
        logger.info(f"🏥 Healthcheck server running on port {port}")
        app.run(
            host='0.0.0.0',
            port=port,
            debug=False,
            use_reloader=False
        )

    except ImportError:
        logger.warning("⚠️ Flask نصب نیست. Healthcheck غیرفعال است.")
    except Exception as e:
        logger.error(f"❌ خطا در healthcheck server: {e}")


# ==============================
# اجرای News Scheduler (async-safe)
# ==============================
async def start_news_scheduler():
    """
    اجرای news_scheduler به صورت async-safe
    """
    try:
        from news_scheduler import start_scheduler

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, start_scheduler)

        logger.info("✅ News scheduler started")

    except ImportError as e:
        logger.error(f"❌ خطا در import news_scheduler: {e}")
    except Exception as e:
        logger.error(f"❌ خطا در اجرای news_scheduler: {e}")


# ==============================
# اجرای Admin Bot
# ==============================
async def start_admin_bot():
    """
    اجرای پنل مدیریت admin_bot به صورت async
    """
    try:
        from admin_bot import app as admin_app

        await admin_app.initialize()
        await admin_app.start()
        await admin_app.updater.start_polling(drop_pending_updates=True)

        logger.info("✅ Admin bot started")

    except ImportError as e:
        logger.error(f"❌ خطا در import admin_bot: {e}")
    except Exception as e:
        logger.error(f"❌ خطا در اجرای admin_bot: {e}")


# ==============================
# Main Async
# ==============================
async def main_async():
    print("\n" + "=" * 70)
    print("🎬 ربات خبری سینما - راه‌اندازی کامل")
    print("=" * 70)

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

    print("\n🧹 پاکسازی و آماده‌سازی ربات...")
    cleanup_success = await cleanup_bot()
    if not cleanup_success:
        print("⚠️ پاکسازی کامل نبود، ادامه می‌دهیم...")

    print("\n📋 سرویس‌های فعال:")
    print("  1️⃣ Admin Bot")
    print("  2️⃣ News Scheduler")
    print("  3️⃣ Healthcheck Server (8080)")
    print("\n🛑 خروج: CTRL+C\n")

    # Healthcheck server در thread جدا
    Thread(
        target=start_healthcheck_server,
        daemon=True
    ).start()

    # اجرای همزمان سرویس‌ها
    await asyncio.gather(
        start_news_scheduler(),
        start_admin_bot()
    )


# ==============================
# Entry Point (برای startup.py و اجرای مستقیم)
# ==============================
def main():
    """
    Entry point استاندارد برای import شدن
    """
    asyncio.run(main_async())


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 ربات متوقف شد. خداحافظ!")
    except Exception as e:
        logger.error("❌ خطای غیرمنتظره", exc_info=True)
        print(f"\n❌ خطای غیرمنتظره: {e}")
