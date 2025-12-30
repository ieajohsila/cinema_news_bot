import os
import asyncio
import logging
from threading import Thread

from telegram import Bot
from telegram.error import TelegramError

# ======================
# Logging
# ======================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("cinema_bot")


# ======================
# Cleanup
# ======================
async def cleanup_bot():
    token = os.getenv("BOT_TOKEN")
    if not token:
        logger.error("❌ BOT_TOKEN تنظیم نشده")
        return False

    bot = Bot(token=token)

    try:
        logger.info("🧹 حذف webhook و pending updates...")

        await bot.delete_webhook(drop_pending_updates=True)

        updates = await bot.get_updates(timeout=2)
        if updates:
            last_id = updates[-1].update_id
            await bot.get_updates(offset=last_id + 1, timeout=2)
            logger.info(f"✅ {len(updates)} pending update پاک شد")
        else:
            logger.info("✅ pending update وجود ندارد")

        me = await bot.get_me()
        logger.info(f"✅ اتصال موفق: @{me.username}")
        return True

    except TelegramError as e:
        logger.error(f"❌ خطا در cleanup: {e}")
        return False
    except Exception:
        logger.exception("❌ خطای غیرمنتظره در cleanup")
        return False


# ======================
# Healthcheck
# ======================
def start_healthcheck():
    try:
        from flask import Flask, jsonify

        app = Flask(__name__)

        @app.route("/")
        def home():
            return "Cinema News Bot is running"

        @app.route("/health")
        def health():
            return jsonify({"status": "ok"}), 200

        port = int(os.getenv("PORT", "8080"))
        logger.info(f"🏥 Healthcheck on port {port}")
        app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

    except ImportError:
        logger.warning("⚠️ Flask نصب نیست، healthcheck غیرفعال شد")
    except Exception:
        logger.exception("❌ خطا در healthcheck")


# ======================
# Admin Bot Runner
# ======================
async def run_admin_bot():
    from admin_bot import create_admin_app

    while True:
        try:
            app = create_admin_app()

            logger.info("🚀 Admin bot starting...")
            await app.initialize()
            await app.start()

            await app.run_polling(
                drop_pending_updates=True,
                close_loop=False
            )

        except Exception:
            logger.exception("❌ Admin bot crash کرد، تلاش مجدد در 5 ثانیه...")
            await asyncio.sleep(5)


# ======================
# News Scheduler Runner
# ======================
async def run_news_scheduler():
    while True:
        try:
            from news_scheduler import run_scheduler
            logger.info("📰 News scheduler starting...")
            await run_scheduler()

        except Exception:
            logger.exception("❌ Scheduler crash کرد، ری‌استارت در 10 ثانیه...")
            await asyncio.sleep(10)


# ======================
# Main Async
# ======================
async def main_async():
    logger.info("=" * 60)
    logger.info("🎬 Cinema News Bot – Hybrid Production Version")
    logger.info("=" * 60)

    if not os.getenv("BOT_TOKEN"):
        raise RuntimeError("BOT_TOKEN تنظیم نشده")

    if not os.getenv("GEMINI_API_KEY"):
        logger.warning("⚠️ GEMINI_API_KEY تنظیم نشده – ترجمه غیرفعال است")

    await cleanup_bot()

    Thread(target=start_healthcheck, daemon=True).start()

    logger.info("📋 سرویس‌های فعال:")
    logger.info("  • Admin Bot")
    logger.info("  • News Scheduler")
    logger.info("  • Healthcheck Server")

    await asyncio.gather(
        run_admin_bot(),
        run_news_scheduler()
    )


# ======================
# Entry Point
# ======================
def main():
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        logger.info("👋 Shutdown")
    except Exception:
        logger.exception("❌ Fatal error")


if __name__ == "__main__":
    main()
