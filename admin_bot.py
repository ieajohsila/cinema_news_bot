from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from database import set_setting, get_setting
from default_sources import DEFAULT_RSS_SOURCES, DEFAULT_SCRAPE_SITES

ADMIN_ID = 81155585  # آیدی عددی شما

# مقداردهی اولیه منابع اگر دیتابیس خالی بود
if not get_setting("rss_sources"):
    set_setting("rss_sources", DEFAULT_RSS_SOURCES)

if not get_setting("scrape_sites"):
    set_setting("scrape_sites", DEFAULT_SCRAPE_SITES)

# ====================== START ======================
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

# ====================== CALLBACK HANDLER ======================
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "set_importance":
        await query.message.reply_text("لطفاً حداقل سطح اهمیت ارسال خبر را وارد کنید (0 تا 3):")
        context.user_data["awaiting_importance"] = True

    elif query.data == "set_target":
        await query.message.reply_text("لطفاً آیدی عددی گروه یا کانال مقصد را ارسال کنید (مثلاً: -1001234567890):")
        context.user_data["awaiting_target"] = True

    elif query.data == "remove_source":
        rss_sources = get_setting("rss_sources") or []
        scrape_sites = get_setting("scrape_sites") or []
        all_sources = rss_sources + scrape_sites
        if not all_sources:
            await query.message.reply_text("هیچ منبعی وجود ندارد.")
            return

        keyboard = [
            [InlineKeyboardButton(src, callback_data=f"del_{i}")]
            for i, src in enumerate(all_sources)
        ]
        await query.message.reply_text("منبعی که می‌خواهید حذف کنید را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))

    # افزودن RSS/Scrape می‌تواند مشابه باشد
    elif query.data == "add_rss":
        await query.message.reply_text("لطفاً لینک RSS جدید را ارسال کنید:")
        context.user_data["awaiting_add_rss"] = True
    elif query.data == "add_scrape":
        await query.message.reply_text("لطفاً آدرس سایت Scraping جدید را ارسال کنید:")
        context.user_data["awaiting_add_scrape"] = True

    # حذف منبع
    elif query.data.startswith("del_"):
        index = int(query.data.split("_")[1])
        rss_sources = get_setting("rss_sources") or []
        scrape_sites = get_setting("scrape_sites") or []
        all_sources = rss_sources + scrape_sites

        source_to_delete = all_sources[index]
        if index < len(rss_sources):
            rss_sources.pop(index)
            set_setting("rss_sources", rss_sources)
        else:
            scrape_sites.pop(index - len(rss_sources))
            set_setting("scrape_sites", scrape_sites)

        await query.message.reply_text(f"منبع '{source_to_delete}' حذف شد.")

# ====================== MESSAGE HANDLER ======================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    # دریافت اهمیت
    if context.user_data.get("awaiting_importance"):
        if text in ["0","1","2","3"]:
            set_setting("min_importance", text)
            await update.message.reply_text(f"حداقل سطح اهمیت روی {text} تنظیم شد.")
        else:
            await update.message.reply_text("مقدار نامعتبر! فقط 0 تا 3 مجاز است.")
        context.user_data["awaiting_importance"] = False

    # دریافت گروه/کانال مقصد
    elif context.user_data.get("awaiting_target"):
        try:
            chat_id = int(text)
            set_setting("TARGET_CHAT_ID", chat_id)
            await update.message.reply_text(f"گروه/کانال مقصد روی {chat_id} تنظیم شد.\nیک پیام تست ارسال می‌کنیم...")
            # ارسال پیام تست
            await context.bot.send_message(chat_id=chat_id, text="ربات با موفقیت به این گروه/کانال متصل شد.")
        except Exception as e:
            await update.message.reply_text(f"خطا در اتصال به گروه/کانال: {e}")
        context.user_data["awaiting_target"] = False

    # افزودن RSS
    elif context.user_data.get("awaiting_add_rss"):
        rss_sources = get_setting("rss_sources") or []
        rss_sources.append(text)
        set_setting("rss_sources", rss_sources)
        await update.message.reply_text(f"RSS '{text}' اضافه شد.")
        context.user_data["awaiting_add_rss"] = False

    # افزودن Scrape
    elif context.user_data.get("awaiting_add_scrape"):
        scrape_sites = get_setting("scrape_sites") or []
        scrape_sites.append(text)
        set_setting("scrape_sites", scrape_sites)
        await update.message.reply_text(f"سایت Scraping '{text}' اضافه شد.")
        context.user_data["awaiting_add_scrape"] = False

# ====================== RUN ======================
if __name__ == "__main__":
    import os
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Admin Bot running...")
    app.run_polling()
