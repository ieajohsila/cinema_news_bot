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
from importance import (
    get_all_rules,
    get_level_keywords,
    add_keyword,
    remove_keyword,
    add_new_level,
)
from status_handler import get_status_message

ADMIN_ID = 81155585  # آیدی عددی ادمین

# =========================
# ابزار کمکی
# =========================
def is_admin(update: Update) -> bool:
    return update.effective_user and update.effective_user.id == ADMIN_ID

def get_main_menu_keyboard():
    """دریافت کیبورد منوی اصلی"""
    return [
        [InlineKeyboardButton("📊 وضعیت ربات", callback_data="status")],
        [InlineKeyboardButton("📋 نمایش منابع", callback_data="list_sources")],
        [
            InlineKeyboardButton("➕ افزودن RSS", callback_data="add_rss"),
            InlineKeyboardButton("➕ افزودن Scraping", callback_data="add_scrape"),
        ],
        [InlineKeyboardButton("❌ حذف منبع", callback_data="remove_source")],
        [InlineKeyboardButton("🎯 تنظیم کانال مقصد", callback_data="set_target")],
        [InlineKeyboardButton("⚙️ تنظیم حداقل اهمیت", callback_data="set_min_importance")],
        [InlineKeyboardButton("🔧 مدیریت کلمات کلیدی", callback_data="manage_keywords")],
        [InlineKeyboardButton("⏰ تنظیمات زمان‌بندی", callback_data="scheduling_settings")],
        # دکمه‌های جدید تست
        [InlineKeyboardButton("📰 ارسال خبر تست", callback_data="send_test_news")],
        [InlineKeyboardButton("📊 ارسال ترند تست", callback_data="send_test_trend")],
    ]

# =========================
# /start — پنل اصلی
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("⛔️ شما دسترسی به این ربات ندارید.")
        return

    keyboard = get_main_menu_keyboard()

    await update.message.reply_text(
        "🎬 *پنل مدیریت ربات خبری سینما*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def show_main_menu(query):
    """نمایش منوی اصلی از callback"""
    keyboard = get_main_menu_keyboard()
    
    try:
        await query.edit_message_text(
            "🎬 *پنل مدیریت ربات خبری سینما*",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    except:
        await query.message.reply_text(
            "🎬 *پنل مدیریت ربات خبری سینما*",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

# =========================
# وضعیت ربات
# =========================
async def show_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
    
    msg = get_status_message()
    
    keyboard = [
        [InlineKeyboardButton("🔄 بروزرسانی", callback_data="status")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")]
    ]
    
    if query:
        try:
            await query.edit_message_text(
                msg,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        except:
            await query.message.reply_text(
                msg,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
    else:
        await update.message.reply_text(
            msg,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

# =========================
# نمایش منابع
# =========================
async def list_sources(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query if hasattr(update, 'callback_query') else None
    
    if not is_admin(update):
        return
    
    rss = get_rss_sources()
    scrape = get_scrape_sources()
    
    msg = "📋 *منابع فعال:*\n\n"
    
    if rss:
        msg += f"📰 *RSS Sources ({len(rss)}):*\n"
        for i, url in enumerate(rss, 1):
            msg += f"{i}. `{url}`\n"
        msg += "\n"
    else:
        msg += "📰 *RSS Sources:* هیچ منبعی یافت نشد\n\n"
    
    if scrape:
        msg += f"🕷️ *Scrape Sources ({len(scrape)}):*\n"
        for i, url in enumerate(scrape, 1):
            msg += f"{i}. `{url}`\n"
    else:
        msg += "🕷️ *Scrape Sources:* هیچ منبعی یافت نشد"
    
    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")]]
    
    if query:
        try:
            await query.edit_message_text(
                msg, 
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        except:
            await query.message.reply_text(
                msg,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
    else:
        await update.message.reply_text(
            msg,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

# =========================
# مدیریت کلمات کلیدی و منوها (همه چیز بدون تغییر)
# =========================
# ... [تمام توابع مربوط به manage_keywords_menu، show_level_keywords، show_remove_source_menu، scheduling_settings_menu بدون تغییر باقی می‌مانند] ...

# =========================
# Callback دکمه‌ها - اضافه کردن دکمه‌های تست
# =========================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_admin(update):
        return

    data = query.data

    # بازگشت به منوی اصلی
    if data == "back_to_main":
        await show_main_menu(query)
        return

    # وضعیت
    elif data == "status":
        await show_status(update, context)

    # منابع
    elif data == "list_sources":
        await list_sources(update, context)

    # افزودن RSS و Scrape
    elif data == "add_rss":
        context.user_data.clear()
        context.user_data["awaiting_add_rss"] = True
        await query.message.reply_text("📰 آدرس RSS را ارسال کنید:")

    elif data == "add_scrape":
        context.user_data.clear()
        context.user_data["awaiting_add_scrape"] = True
        await query.message.reply_text("🕷️ آدرس سایت Scraping را ارسال کنید:")

    elif data == "remove_source":
        await show_remove_source_menu(query)

    # تنظیمات و مدیریت کلمات کلیدی ...
    # [همه callbackهای قبلی بدون تغییر باقی می‌مانند]

    # =====================
    # دکمه‌های تست
    # =====================
    elif data == "send_test_news":
        rss_sources = get_rss_sources()
        scrape_sources = get_scrape_sources()

        news_item = None
        if rss_sources:
            news_item = f"✅ این یک خبر تست از RSS است: {rss_sources[0]}"
        elif scrape_sources:
            news_item = f"✅ این یک خبر تست از Scraping است: {scrape_sources[0]}"
        else:
            news_item = "❌ هیچ منبعی برای تست یافت نشد."

        await query.message.reply_text(news_item)
        return

    elif data == "send_test_trend":
        test_trends = [
            "🎬 تست ترند 1",
            "🎬 تست ترند 2",
            "🎬 تست ترند 3"
        ]
        msg = "📊 *لیست ترند تست:*\n\n" + "\n".join(test_trends)
        await query.message.reply_text(msg, parse_mode="Markdown")
        return

# =========================
# پیام‌های متنی بدون تغییر
# =========================
async def receive_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # [تمام دریافت پیام‌های متنی مثل RSS، Scrape، تنظیمات و کلمات کلیدی بدون تغییر باقی می‌مانند]
    pass

# =========================
# ساخت Application
# =========================
def create_app():
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        raise RuntimeError("❌ BOT_TOKEN تنظیم نشده است")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", show_status))
    app.add_handler(CommandHandler("sources", list_sources))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_message))

    return app

app = create_app()

if __name__ == "__main__":
    print("🤖 ربات در حال اجرا...")
    app.run_polling()
