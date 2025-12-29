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
    get_collected_news,      # جدید: گرفتن اخبار جمع‌آوری شده
)
from importance import (
    get_all_rules,
    get_level_keywords,
    add_keyword,
    remove_keyword,
    add_new_level,
)
from status_handler import get_status_message

ADMIN_ID = 81155585  # آیدی ادمین

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
        [InlineKeyboardButton("📰 ارسال خبر تست", callback_data="send_test_news")],
        [InlineKeyboardButton("📈 ارسال ترند تست", callback_data="send_test_trends")],
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
# ارسال خبر تست واقعی
# =========================
async def send_test_news(query):
    """جمع‌آوری و نمایش آخرین اخبار جمع‌آوری‌شده"""
    await query.answer()
    news = get_collected_news(limit=1)  # آخرین خبر
    
    if not news:
        await query.message.reply_text("❌ هیچ خبری جمع‌آوری نشده است.")
        return

    n = news[0]
    msg = f"📰 *خبر تست واقعی*\n\n"
    msg += f"*عنوان:* {n['title']}\n"
    msg += f"*خلاصه:* {n.get('summary', '')}\n"
    msg += f"*لینک:* [مشاهده]({n['url']})\n"
    if 'translated' in n:
        msg += f"\n*ترجمه:* {n['translated']}"

    await query.message.reply_text(msg, parse_mode="Markdown", disable_web_page_preview=False)


# =========================
# ارسال ترند تست واقعی
# =========================
async def send_test_trends(query):
    """محاسبه و نمایش ترندهای واقعی"""
    await query.answer()
    news = get_collected_news()
    if not news:
        await query.message.reply_text("❌ هیچ خبری جمع‌آوری نشده است.")
        return

    # ترند: بیشترین تعداد تکرار در عنوان اخبار
    title_count = {}
    for n in news:
        t = n['title']
        title_count[t] = title_count.get(t, 0) + 1

    sorted_trends = sorted(title_count.items(), key=lambda x: x[1], reverse=True)[:10]
    msg = "📈 *ترندهای فعلی اخبار*:\n\n"
    for title, count in sorted_trends:
        msg += f"• {title} ({count} بار)\n"

    await query.message.reply_text(msg, parse_mode="Markdown")


# =========================
# Callback دکمه‌ها
# =========================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_admin(update):
        return

    data = query.data

    if data == "back_to_main":
        await show_main_menu(query)
        return
    elif data == "status":
        await show_status(update, context)
        return
    elif data == "list_sources":
        await list_sources(update, context)
        return
    elif data == "send_test_news":
        await send_test_news(query)
        return
    elif data == "send_test_trends":
        await send_test_trends(query)
        return

    # سایر callbackهای موجود (افزودن RSS، Scrape، مدیریت کلمات، زمان‌بندی و …)
    # ... کدهای قبلی button_handler بدون تغییر اضافه میشن

# =========================
# ساخت Application
# =========================
def create_app():
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        raise RuntimeError("❌ BOT_TOKEN تنظیم نشده است")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_message))

    return app


app = create_app()

if __name__ == "__main__":
    print("🤖 ربات در حال اجرا...")
    app.run_polling()
