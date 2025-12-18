import os
from datetime import datetime, timedelta
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


def format_timedelta(td):
    """تبدیل timedelta به فرمت خوانا"""
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    
    if hours > 0:
        return f"{hours} ساعت و {minutes} دقیقه"
    elif minutes > 0:
        return f"{minutes} دقیقه"
    else:
        return f"{total_seconds} ثانیه"


# =========================
# /start — پنل اصلی
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("⛔️ شما دسترسی به این ربات ندارید.")
        return

    keyboard = [
        [InlineKeyboardButton("📊 وضعیت ربات", callback_data="status")],
        [InlineKeyboardButton("📋 نمایش منابع", callback_data="list_sources")],
        [InlineKeyboardButton("➕ افزودن RSS", callback_data="add_rss")],
        [InlineKeyboardButton("➕ افزودن Scraping", callback_data="add_scrape")],
        [InlineKeyboardButton("❌ حذف منبع", callback_data="remove_source")],
        [InlineKeyboardButton("🎯 تنظیم گروه/کانال مقصد", callback_data="set_target")],
        [InlineKeyboardButton("⚙️ مدیریت اهمیت اخبار", callback_data="set_importance")],
    ]

    await update.message.reply_text(
        "🎬 پنل مدیریت ربات خبری سینما\n\n"
        "از دکمه‌های زیر برای مدیریت ربات استفاده کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# =========================
# نمایش وضعیت ربات
# =========================
async def show_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش وضعیت کامل ربات"""
    if not is_admin(update):
        return
    
    # دریافت تنظیمات
    target_chat = get_setting("TARGET_CHAT_ID") or "❌ تنظیم نشده"
    min_importance = get_setting("min_importance") or "1"
    
    # دریافت آخرین زمان‌ها از دیتابیس
    last_fetch_str = get_setting("last_news_fetch")
    last_send_str = get_setting("last_news_send")
    next_trend_str = get_setting("next_trend_time")
    
    # تعداد منابع
    rss_count = len(get_rss_sources())
    scrape_count = len(get_scrape_sources())
    
    # محاسبه زمان بعدی جمع‌آوری
    news_interval_hours = 3  # از تنظیمات news_scheduler
    if last_fetch_str:
        try:
            last_fetch = datetime.fromisoformat(last_fetch_str)
            next_fetch = last_fetch + timedelta(hours=news_interval_hours)
            now = datetime.now()
            
            if next_fetch > now:
                time_until_fetch = format_timedelta(next_fetch - now)
                next_fetch_text = f"⏰ {time_until_fetch} دیگر"
            else:
                next_fetch_text = "🔄 در حال اجرا..."
        except:
            next_fetch_text = "❓ نامشخص"
    else:
        next_fetch_text = "⏳ هنوز شروع نشده"
    
    # محاسبه زمان بعدی ترند
    if next_trend_str:
        try:
            next_trend = datetime.fromisoformat(next_trend_str)
            now = datetime.now()
            
            if next_trend > now:
                time_until_trend = format_timedelta(next_trend - now)
                next_trend_text = f"⏰ {time_until_trend} دیگر\n   📅 {next_trend.strftime('%Y-%m-%d ساعت %H:%M')}"
            else:
                next_trend_text = "🔄 در حال اجرا..."
        except:
            next_trend_text = "❓ نامشخص"
    else:
        next_trend_text = "⏳ هنوز شروع نشده"
    
    # فرمت آخرین ارسال
    if last_send_str:
        try:
            last_send = datetime.fromisoformat(last_send_str)
            last_send_text = last_send.strftime('%Y-%m-%d ساعت %H:%M')
        except:
            last_send_text = "❓ نامشخص"
    else:
        last_send_text = "⏳ هنوز ارسال نشده"
    
    # ساخت پیام وضعیت
    msg = "📊 *وضعیت ربات خبری سینما*\n"
    msg += "═" * 30 + "\n\n"
    
    msg += "🎯 *تنظیمات:*\n"
    msg += f"   📤 مقصد: `{target_chat}`\n"
    msg += f"   ⭐️ حداقل اهمیت: {min_importance}\n\n"
    
    msg += "📰 *منابع خبری:*\n"
    msg += f"   🟢 RSS: {rss_count} منبع\n"
    msg += f"   🔵 Scraping: {scrape_count} منبع\n\n"
    
    msg += "⏰ *زمان‌بندی:*\n"
    msg += f"   🔄 جمع‌آوری بعدی: {next_fetch_text}\n"
    msg += f"   📊 ارسال ترند بعدی: {next_trend_text}\n"
    msg += f"   ✅ آخرین ارسال: {last_send_text}\n\n"
    
    msg += "═" * 30 + "\n"
    msg += f"🕐 به‌روزرسانی: {datetime.now().strftime('%H:%M:%S')}"
    
    # دکمه رفرش
    keyboard = [[InlineKeyboardButton("🔄 به‌روزرسانی", callback_data="status")]]
    
    if update.callback_query:
        await update.callback_query.message.edit_text(
            msg, 
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text(
            msg,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


# =========================
# نمایش منابع
# =========================
async def list_sources(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش تمام منابع فعال"""
    if not is_admin(update):
        return
    
    rss = get_rss_sources()
    scrape = get_scrape_sources()
    
    msg = "📋 *منابع فعال:*\n\n"
    
    if rss:
        msg += f"📰 *RSS Sources ({len(rss)}):*\n"
        for i, url in enumerate(rss, 1):
            msg += f"{i}. {url}\n"
        msg += "\n"
    else:
        msg += "📰 *RSS Sources:* هیچ منبعی یافت نشد\n\n"
    
    if scrape:
        msg += f"🕷️ *Scrape Sources ({len(scrape)}):*\n"
        for i, url in enumerate(scrape, 1):
            msg += f"{i}. {url}\n"
    else:
        msg += "🕷️ *Scrape Sources:* هیچ منبعی یافت نشد"
    
    if update.callback_query:
        await update.callback_query.message.reply_text(msg, parse_mode="Markdown")
    else:
        await update.message.reply_text(msg, parse_mode="Markdown")


# =========================
# Callback دکمه‌ها
# =========================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_admin(update):
        return

    if query.data == "status":
        await show_status(update, context)

    elif query.data == "add_rss":
        context.user_data.clear()
        context.user_data["awaiting_add_rss"] = True
        await query.message.reply_text("آدرس RSS را ارسال کنید:")

    elif query.data == "add_scrape":
        context.user_data.clear()
        context.user_data["awaiting_add_scrape"] = True
        await query.message.reply_text("آدرس سایت Scraping را ارسال کنید:")

    elif query.data == "remove_source":
        await show_remove_source_menu(query.message)

    elif query.data == "list_sources":
        await list_sources(update, context)

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
        display_url = url[:60] + "..." if len(url) > 60 else url
        keyboard.append(
            [InlineKeyboardButton(f"🟢 RSS | {display_url}", callback_data=f"del_rss|{url}")]
        )

    for url in scrape:
        display_url = url[:60] + "..." if len(url) > 60 else url
        keyboard.append(
            [InlineKeyboardButton(f"🔵 Scrape | {display_url}", callback_data=f"del_scrape|{url}")]
        )

    if not keyboard:
        await message.reply_text("هیچ منبعی برای حذف وجود ندارد.\n\n💡 برای افزودن منبع از دکمه‌های پنل اصلی استفاده کنید.")
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
        await query.edit_message_text(f"✅ منبع RSS حذف شد:\n{url}")

    elif data.startswith("del_scrape|"):
        url = data.split("|", 1)[1]
        remove_scrape_source(url)
        await query.edit_message_text(f"✅ منبع Scraping حذف شد:\n{url}")


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
        await update.message.reply_text(f"✅ RSS اضافه شد:\n{text}")
        return

    # افزودن Scraping
    if context.user_data.get("awaiting_add_scrape"):
        add_scrape_source(text)
        context.user_data.clear()
        await update.message.reply_text(f"✅ منبع Scraping اضافه شد:\n{text}")
        return

    # تنظیم اهمیت
    if context.user_data.get("awaiting_importance"):
        if text in {"0", "1", "2", "3"}:
            set_setting("min_importance", text)
            await update.message.reply_text(f"✅ حداقل اهمیت روی {text} تنظیم شد.")
        else:
            await update.message.reply_text("❌ عدد نامعتبر است. فقط 0 تا 3 مجاز است.")
        context.user_data.clear()
        return

    # تنظیم مقصد
    if context.user_data.get("awaiting_target"):
        set_setting("TARGET_CHAT_ID", text)
        context.user_data.clear()
        await update.message.reply_text(
            f"✅ مقصد تنظیم شد: {text}\n📤 در حال ارسال پیام تست..."
        )

        try:
            await context.bot.send_message(
                chat_id=int(text),
                text="✅ اتصال موفق است. این پیام تست از ربات خبری سینماست.",
            )
            await update.message.reply_text("✅ پیام تست با موفقیت ارسال شد!")
        except Exception as e:
            await update.message.reply_text(f"❌ ارسال پیام تست ناموفق بود:\n{e}")
        return


# =========================
# ساخت Application
# =========================
def create_app():
    """ساخت و تنظیم Application"""
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        raise RuntimeError("❌ BOT_TOKEN در Environment Variables تنظیم نشده است")

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # ترتیب بسیار مهم است
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", show_status))
    application.add_handler(CommandHandler("sources", list_sources))
    application.add_handler(CallbackQueryHandler(remove_source_callback, pattern=r"^del_"))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_message))

    return application


# برای import کردن در main.py
app = create_app()


# =========================
# اجرای مستقیم (اگر بخواهید فقط admin_bot اجرا شود)
# =========================
if __name__ == "__main__":
    print("🤖 ربات خبری سینما در حال راه‌اندازی...")
    print("✅ ربات آماده است و منتظر دریافت پیام...")
    app.run_polling()
