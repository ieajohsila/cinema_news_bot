import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from database import (
    get_rss_sources, add_rss_source, remove_rss_source,
    get_scrape_sources, add_scrape_source, remove_scrape_source,
    is_sent, mark_sent,
    get_setting, set_setting
)

ADMIN_ID = 81155585  # آیدی عددی شما

# ---- دستورات ادمین ----
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    keyboard = [
        [InlineKeyboardButton("➕ افزودن RSS", callback_data="add_rss")],
        [InlineKeyboardButton("➕ افزودن Scraping", callback_data="add_scrape")],
        [InlineKeyboardButton("❌ حذف منبع", callback_data="remove_source")],
        [InlineKeyboardButton("🎯 تنظیم گروه/کانال مقصد", callback_data="set_target")],
        [InlineKeyboardButton("⚙️ مدیریت اهمیت اخبار", callback_data="set_importance")]
    ]
    await update.message.reply_text(
        "پنل مدیریت ربات خبری:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ---- مدیریت اهمیت اخبار ----
async def set_importance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "لطفاً حداقل سطح اهمیت ارسال خبر را وارد کنید (0 تا 3):"
    )
    context.user_data["awaiting_importance"] = True

async def receive_importance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_importance"):
        val = update.message.text.strip()
        if val in ["0", "1", "2", "3"]:
            set_setting("min_importance", val)
            await update.message.reply_text(f"حداقل سطح اهمیت روی {val} تنظیم شد.")
        context.user_data["awaiting_importance"] = False

# ---- تنظیم گروه/کانال مقصد ----
async def set_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "لطفاً آیدی عددی گروه یا کانال مقصد را ارسال کنید (مثلاً: -1001234567890):"
    )
    context.user_data["awaiting_target"] = True

async def receive_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_target"):
        val = update.message.text.strip()
        set_setting("TARGET_CHAT_ID", val)
        context.user_data["awaiting_target"] = False
        await update.message.reply_text(f"گروه/کانال مقصد روی {val} تنظیم شد. ارسال پیام تست...")
        # پیام تست
        try:
            await context.bot.send_message(chat_id=int(val), text="این یک پیام تست از ربات خبری است ✅")
        except Exception as e:
            await update.message.reply_text(f"ارسال پیام تست ناموفق بود: {e}")

# ---- حذف منبع ----
async def remove_source_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rss = get_rss_sources()
    scrape = get_scrape_sources()
    keyboard = []

    for url in rss:
        keyboard.append([InlineKeyboardButton(f"RSS: {url}", callback_data=f"del_rss|{url}")])
    for url in scrape:
        keyboard.append([InlineKeyboardButton(f"Scrape: {url}", callback_data=f"del_scrape|{url}")])

    if not keyboard:
        await update.message.reply_text("منبعی برای حذف وجود ندارد.")
        return

    await update.message.reply_text("روی منبعی که می‌خواهید حذف شود کلیک کنید:", reply_markup=InlineKeyboardMarkup(keyboard))

async def remove_source_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data.startswith("del_rss|"):
        url = data.split("|")[1]
        remove_rss_source(url)
        await query.edit_message_text(f"منبع RSS حذف شد:\n{url}")
    elif data.startswith("del_scrape|"):
        url = data.split("|")[1]
        remove_scrape_source(url)
        await query.edit_message_text(f"منبع Scrape حذف شد:\n{url}")

# ---- Callback اصلی ----
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "add_rss":
        await query.message.reply_text("لطفاً آدرس RSS را ارسال کنید:")
        context.user_data["awaiting_add_rss"] = True
    elif query.data == "add_scrape":
        await query.message.reply_text("لطفاً آدرس سایت Scraping را ارسال کنید:")
        context.user_data["awaiting_add_scrape"] = True
    elif query.data == "remove_source":
        await remove_source_menu(update, context)
    elif query.data == "set_target":
        await set_target(update, context)
    elif query.data == "set_importance":
        await set_importance(update, context)

# ---- دریافت پیام‌ها برای افزودن منابع ----
async def receive_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if context.user_data.get("awaiting_add_rss"):
        add_rss_source(text)
        await update.message.reply_text(f"RSS اضافه شد:\n{text}")
        context.user_data["awaiting_add_rss"] = False
    elif context.user_data.get("awaiting_add_scrape"):
        add_scrape_source(text)
        await update.message.reply_text(f"Scraping اضافه شد:\n{text}")
        context.user_data["awaiting_add_scrape"] = False
    elif context.user_data.get("awaiting_importance"):
        await receive_importance(update, context)
    elif context.user_data.get("awaiting_target"):
        await receive_target(update, context)

# ---- ایجاد اپلیکیشن ----
if __name__ == "__main__":
    BOT_TOKEN = os.getenv("BOT_TOKEN")  # یا قرار بده مستقیم
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_message))
    app.add_handler(CallbackQueryHandler(remove_source_callback, pattern=r"del_"))

    app.run_polling()
