# main.py
import os
import asyncio
import logging
from threading import Thread

from telegram import Bot
from telegram.error import TelegramError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("main")


# ======================
# Cleanup
# ======================
async def cleanup_bot():
    token = os.getenv("BOT_TOKEN")
    if not token:
        logger.error("❌ BOT_TOKEN تنظیم نشده")
        return

    bot = Bot(token=token)
    try:
        logger.info("🧹 حذف webhook و pending updates...")
        await bot.delete_webhook(drop_pending_updates=True)
        await bot.get_updates(timeout=1)
        me = await bot.get_me()
        logger.info(f"✅ اتصال موفق: @{me.username}")
    except TelegramError as e:
        logger.warning(f"⚠️ cleanup ناقص: {e}")


# ======================
# Healthcheck
# ======================
def start_healthcheck():
    from flask import Flask, jsonify

    app = Flask(__name__)

    @app.route("/")
    def home():
        return "Cinema News Bot is running"

    @app.route("/health")
    def health():
        return jsonify({"status": "ok"}), 200

    port = int(os.getenv("PORT", 8080))
    logger.info(f"🏥 Healthcheck on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)


# ======================
# Admin Bot
# ======================
async def run_admin_bot():
    from admin_bot import create_admin_app

    while True:
        try:
            app = create_admin_app()
            logger.info("🚀 Admin bot starting...")

            await app.run_polling(
                drop_pending_updates=True,
                close_loop=False
            )

        except Exception:
            logger.exception("❌ Admin bot crash کرد، تلاش مجدد در 5 ثانیه...")
            await asyncio.sleep(5)



# ======================
# Scheduler
# ======================
async def run_news_scheduler():
    from news_scheduler import run_scheduler
    await run_scheduler()


# ======================
# Main
# ======================
async def main_async():
    if not os.getenv("BOT_TOKEN"):
        raise RuntimeError("BOT_TOKEN تنظیم نشده")

    await cleanup_bot()

    Thread(target=start_healthcheck, daemon=True).start()

    await asyncio.gather(
        run_admin_bot(),
        run_news_scheduler()
    )


def main():
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        logger.info("👋 Shutdown")
    except Exception:
        logger.error("❌ Fatal error", exc_info=True)


if __name__ == "__main__":
    main()
