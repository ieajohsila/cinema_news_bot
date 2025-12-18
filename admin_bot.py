# admin_bot.py
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)
from database import set_setting, get_setting  # فرض بر این است که این‌ها شما را به DB متصل می‌کنند

ADMIN_ID = 81155585  # آیدی عددی شما

# ----- پنل مدیریت -----
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    keyboard = [
        [InlineKeyboardButton("➕ افزودن RSS", callback_data="add_rss")],
        [InlineKeyboardButton("➕ افزودن سایت Scraping", callback_data="add_scrape")],
        [InlineKeyboardButton("❌ حذف منبع", callback_data="remove_source")],
        [InlineKeyboardButton("🎯 تنظیم گروه/کانال مقصد", callback_data="set_target")],
        [InlineKeyboardButton("⚙️ مدیریت اهمیت اخبار", callback_data="set_importance")]
    ]

    await update.message.reply_text(
        "پنل مدیریت ربات خبری:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ----- افزودن RSS -----
async def add_rss(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.reply_text("لطفاً آدرس RSS را ارسال کنید:")
    context.user_data["awaiting_rss"] = True

async def receive_rss(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_rss"):
        url = update.message.text.strip()
        sources = get_setting("rss_sources") or []
        if url not in sources:
            sources.append(url)
            set_setting("rss_sources", sources)
            await update.message.reply_text(f"RSS اضافه شد: {url}")
        else:
            await update.message.reply_text("این RSS قبلاً اضافه شده است.")
        context.user_data["awaiting_rss"] = False

# ----- افزودن سایت Scraping -----
async def add_scrape(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.reply_text("لطفاً آدرس سایت برای Scraping را ارسال کنید:")
    context.user_data["awaiting_scrape"] = True

async def receive_scrape(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_scrape"):
        url = update.message.text.strip()
        sources = get_setting("scrape_sites") or []
        if url not in sources:
            sources.append(url)
            set_setting("scrape_sites", sources)
            await update.message.reply_text(f"سایت Scraping اضافه شد: {url}")
        else:
            await update.message.reply_text("این سایت قبلاً اضافه شده است.")
        context.user_data["awaiting_scrape"] = False

# ----- حذف منبع -----
async def remove_source(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # نمایش منابع RSS و Scraping با دکمه
    rss_sources = get_setting("rss_sources") or []
    scrape_sources = get_setting("scrape_sites") or []

    keyboard = []
    for src in rss_sources:
        keyboard.append([InlineKeyboardButton(f"RSS: {src}", callback_data=f"delete_rss|{src}")])
    for src in scrape_sources:
        keyboard.append([InlineKeyboardButton(f"Scrape: {src}", callback_data=f"delete_scrape|{src}")])

    if not keyboard:
        await update.callback_query.message.reply_text("هیچ منبعی موجود نیست.")
        return

    await update.callback_query.message.reply_text(
        "لطفاً منبعی که می‌خواهید حذف کنید را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ----- مدیریت اهمیت اخبار -----
async def set_importance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.reply_text(
        "لطفاً حداقل سطح اهمیت ارسال خبر را وارد کنید (0 تا 3):"
    )
    context.user_data["awaiting_importance"] = True

async def receive_importance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_importance"):
        val = update.message.text.strip()
        if val in ["0", "1", "2", "3"]:
            set_setting("min_importance", val)
            await update.message.reply_text(f"حداقل سطح اهمیت روی {val} تنظیم شد.")
        else:
            await update.message.reply_text("مقدار نامعتبر است، لطفاً عددی بین 0 تا 3 وارد کنید.")
        context.user_data["awaiting_importance"] = False

# ----- تنظیم گروه/کانال مقصد -----
async def set_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.reply_text(
        "لطفاً آیدی عددی گروه یا کانال مقصد را ارسال کنید (مثلاً: -1001234567890):"
    )
    context.user_data["awaiting_target"] = True

async def receive_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_target"):
        val = update.message.text.strip()
        set_setting("TARGET_CHAT_ID", val)
        await update.message.reply_text(f"گروه/کانال مقصد روی {val} تنظیم شد.")
        context.user_data["awaiting_target"] = False

# ----- کلیک دکمه‌ها -----
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "add_rss":
        await add_rss(update, context)
    elif query.data == "add_scrape":
        await add_scrape(update, context)
    elif query.data == "remove_source":
        await remove_source(update, context)
    elif query.data == "set_importance":
        await set_importance(update, context)
    elif query.data == "set_target":
        await set_target(update, context)
    # حذف منبع
    elif query.data.startswith("delete_rss|"):
        src = query.data.split("|")[1]
        sources = get_setting("rss_sources") or []
        if src in sources:
            sources.remove(src)
            set_setting("rss_sources", sources)
            await query.message.edit_text(f"منبع حذف شد: {src}")
        else:
            await query.message.edit_text("منبع پیدا نشد.")
    elif query.data.startswith("delete_scrape|"):
        src = query.data.split("|")[1]
        sources = get_setting("scrape_sites") or []
        if src in sources:
            sources.remove(src)
            set_setting("scrape_sites", sources)
            await query.message.edit_text(f"منبع حذف شد: {src}")
        else:
            await query.message.edit_text("منبع پیدا نشد.")

# ----- اجرای اپلیکیشن -----
if __name__ == "__main__":
    BOT_TOKEN = os.getenv("BOT_TOKEN")  # توکن واقعی را داخل ENV بگذارید
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Command ها
    app.add_handler(CommandHandler("start", start))
    # Message ها برای دریافت داده‌ها
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_rss))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_scrape))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_importance))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_target))
    # Callback Query ها
    app.add_handler(CallbackQueryHandler(button_callback))

    app.run_polling()
