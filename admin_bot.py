import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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

ADMIN_ID = 81155585  # آیدی عددی ادمین


# =========================
# ابزار کمکی
# =========================
def is_admin(update: Update) -> bool:
    return update.effective_user and update.effective_user.id == ADMIN_ID


# =========================
# /start — پنل اصلی
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return

    keyboard = [
        [InlineKeyboardButton("➕ افزودن RSS", callback_data="add_rss")],
        [InlineKeyboardButton("➕ افزودن Scraping", callback_data="add_scrape")],
        [InlineKeyboardButton("❌ حذف منبع", callback_data="remove_source")],
        [InlineKeyboardButton("🎯 تنظیم گروه/کانال مقصد", callback_data="set_target")],
        [InlineKeyboardButton("⚙️ مدیریت اهمیت اخبار", callback_data="set_importance")],
    ]

    await update.message.reply_text(
        "پنل مدیریت ربات خبری سینما:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# =========================
# Callback دکمه‌ها
# =========================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_admin(update):
        return

    if query.data == "add_rss":
        context.user_data.clear()
        context.user_data["awaiting_add_rss"] = True
        await query.message.reply_text("آدرس RSS را ارسال کنید:")

    elif query.data == "add_scrape":
        context.user_data.clear()
        context.user_data["awaiting_add_scrape"] = True
        await query.message.reply_text("آدرس سایت Scraping را ارسال کنید:")

    elif query.data == "remove_source":
        await show_remove_source_menu(query.message)

    elif query.data == "set_target":
        context.user_data.clear()
        context.user_data["awaiting_target"] = True
        await query.message.reply_text(
            "آیدی عددی گروه یا کانال مقصد را ارسال کنید (مثلاً: -1001234567890):"
        )

    elif query.data == "set_importance":
        context.user_data.clear()
        context.user_data["awaiting_importance"] = True
        await query.message.reply_text(
            "حداقل سطح اهمیت ارسال خبر را وارد کنید (0 تا 3):"
        )


# =========================
# منوی حذف منبع
# =========================
async def show_remove_source_menu(message):
    rss = get_rss_sources()
    scrape = get_scrape_sources()

    keyboard = []

    for url in rss:
        keyboard.append(
            [InlineKeyboardButton(f"🟢 RSS | {url}", callback_data=f"del_rss|{url}")]
        )

    for url in scrape:
        keyboard.append(
            [InlineKeyboardButton(f"🔵 Scrape | {url}", callback_data=f"del_scrape|{url}")]
        )

    if not keyboard:
        await message.reply_text("هیچ منبعی برای حذف وجود ندارد.")
        return

    await message.reply_text(
        "روی منبع موردنظر برای حذف کلیک کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# =========================
# حذف منبع (Callback خاص)
# =========================
async def remove_source_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_admin(update):
        return

    data = query.data

    if data.startswith("del_rss|"):
        url = data.split("|", 1)[1]
        remove_rss_source(url)
        await query.edit_message_text(f"منبع RSS حذف شد:\n{url}")

    elif data.startswith("del_scrape|"):
        url = data.split("|", 1)[1]
        remove_scrape_source(url)
        await query.edit_message_text(f"منبع Scraping حذف شد:\n{url}")


# =========================
# دریافت پیام‌های متنی ادمین
# =========================
async def receive_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return

    text = update.message.text.strip()

    # افزودن RSS
    if context.user_data.get("awaiting_add_rss"):
        add_rss_source(text)
        context.user_data.clear()
        await update.message.reply_text(f"RSS اضافه شد:\n{text}")
        return

    # افزودن Scraping
    if context.user_data.get("awaiting_add_scrape"):
        add_scrape_source(text)
        context.user_data.clear()
        await update.message.reply_text(f"منبع Scraping اضافه شد:\n{text}")
        return

    # تنظیم اهمیت
    if context.user_data.get("awaiting_importance"):
        if text in {"0", "1", "2", "3"}:
            set_setting("min_importance", text)
            await update.message.reply_text(f"حداقل اهمیت روی {text} تنظیم شد.")
        else:
            await update.message.reply_text("عدد نامعتبر است. فقط 0 تا 3.")
        context.user_data.clear()
        return

    # تنظیم مقصد
    if context.user_data.get("awaiting_target"):
        set_setting("TARGET_CHAT_ID", text)
        context.user_data.clear()
        await update.message.reply_text(
            f"مقصد تنظیم شد: {text}\nدر حال ارسال پیام تست..."
        )

        try:
            await context.bot.send_message(
                chat_id=int(text),
                text="✅ اتصال موفق است. این پیام تست از ربات خبری سینماست.",
            )
        except Exception as e:
            await update.message.reply_text(f"❌ ارسال پیام تست ناموفق بود:\n{e}")
        return


# =========================
# اجرای برنامه
# =========================
if __name__ == "__main__":
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN در Environment Variables تنظیم نشده است")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # ترتیب بسیار مهم است
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(remove_source_callback, pattern=r"^del_"))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_message))

    app.run_polling()
