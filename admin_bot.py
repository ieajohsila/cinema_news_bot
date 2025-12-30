# admin_bot.py
import os
import asyncio
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from database import (
    get_rss_sources,
    add_rss_source,
    remove_rss_source,
    get_scrape_sources,
    add_scrape_source,
    remove_scrape_source,
    get_setting,
    set_setting,
)
from importance import (
    get_all_rules,
    add_keyword,
    remove_keyword,
)
from status_handler import get_status_message
from news_fetcher import fetch_all_news
from news_ranker import rank_news, generate_daily_trend
from translation import translate_title
from category import classify_category
from trends import find_daily_trends, format_trends_message


ADMIN_ID = int(os.getenv("ADMIN_ID", "81155585"))
user_states = {}


# ======================
# Helpers
# ======================
def is_admin(update: Update) -> bool:
    return update.effective_user and update.effective_user.id == ADMIN_ID


def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 وضعیت ربات", callback_data="status")],
        [InlineKeyboardButton("📋 منابع", callback_data="sources")],
        [
            InlineKeyboardButton("➕ RSS", callback_data="add_rss"),
            InlineKeyboardButton("➕ Scrape", callback_data="add_scrape"),
        ],
        [InlineKeyboardButton("❌ حذف منبع", callback_data="remove_source")],
        [InlineKeyboardButton("🎯 تنظیم کانال", callback_data="set_target")],
        [InlineKeyboardButton("⚙️ حداقل اهمیت", callback_data="set_importance")],
        [InlineKeyboardButton("📰 تست خبر", callback_data="test_news")],
        [InlineKeyboardButton("📈 تست ترند", callback_data="test_trends")],
    ])


# ======================
# Commands
# ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("⛔️ دسترسی نداری")
        return

    await update.message.reply_text(
        "🎬 پنل مدیریت ربات خبری سینما",
        reply_markup=main_menu()
    )


# ======================
# Callbacks
# ======================
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_admin(update):
        return

    data = query.data

    if data == "status":
        await query.edit_message_text(
            get_status_message(),
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 بازگشت", callback_data="back")]]
            ),
            parse_mode="Markdown"
        )

    elif data == "sources":
        rss = get_rss_sources()
        scrape = get_scrape_sources()

        msg = f"📰 RSS ({len(rss)}):\n"
        msg += "\n".join(rss[:10]) or "—"
        msg += f"\n\n🕷️ Scrape ({len(scrape)}):\n"
        msg += "\n".join(scrape[:10]) or "—"

        await query.edit_message_text(
            msg,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 بازگشت", callback_data="back")]]
            )
        )

    elif data == "test_news":
        await query.message.reply_text("⏳ جمع‌آوری اخبار...")
        news = fetch_all_news()
        ranked = rank_news(news, int(get_setting("min_importance", "1")))

        for item in ranked[:3]:
            title = translate_title(item["title"])
            link = item.get("link") or item.get("url", "")
            cat = classify_category(item["title"], item.get("summary", ""))
            await query.message.reply_text(
                f"{cat}\n\n*{title}*\n\n🔗 {link}",
                parse_mode="Markdown"
            )
            await asyncio.sleep(1)

    elif data == "test_trends":
        trends = find_daily_trends()
        msg = format_trends_message(trends) if trends else generate_daily_trend(fetch_all_news())
        await query.message.reply_text(msg, parse_mode="Markdown")

    elif data == "back":
        await query.edit_message_text(
            "🎬 پنل مدیریت",
            reply_markup=main_menu()
        )


# ======================
# Text Messages
# ======================
async def receive_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return

    state = user_states.get(ADMIN_ID)
    text = update.message.text

    if text == "/cancel":
        user_states.clear()
        await update.message.reply_text("❌ لغو شد", reply_markup=main_menu())
        return

    if state == "rss":
        add_rss_source(text)
        await update.message.reply_text("✅ RSS اضافه شد")
        user_states.clear()


# ======================
# App Factory
# ======================
def create_admin_app():
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN تنظیم نشده")

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_message))

    return app
