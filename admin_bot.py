import os
import asyncio
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
)
from status_handler import get_status_message
from news_fetcher import fetch_all_news
from news_ranker import rank_news, generate_daily_trend
from translation import translate_title
from category import classify_category
from trends import find_daily_trends, format_trends_message

ADMIN_ID = 81155585  # آیدی ادمین

# متغیر سراسری برای مدیریت حالت دریافت پیام
user_states = {}

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
        [InlineKeyboardButton("📰 تست خبر (3 خبر)", callback_data="send_test_news")],
        [InlineKeyboardButton("📈 تست ترند", callback_data="send_test_trends")],
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
    query = update.callback_query
    await query.answer()
    
    rss_sources = get_rss_sources()
    scrape_sources = get_scrape_sources()
    
    msg = "📋 *منابع فعال:*\n\n"
    msg += f"📰 *RSS ({len(rss_sources)} منبع):*\n"
    
    if rss_sources:
        for i, url in enumerate(rss_sources, 1):
            msg += f"{i}. `{url[:50]}...`\n"
    else:
        msg += "   هیچ منبع RSS تنظیم نشده\n"
    
    msg += f"\n🕷️ *Scraping ({len(scrape_sources)} منبع):*\n"
    
    if scrape_sources:
        for i, url in enumerate(scrape_sources, 1):
            msg += f"{i}. `{url[:50]}...`\n"
    else:
        msg += "   هیچ منبع Scraping تنظیم نشده\n"
    
    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")]]
    
    await query.edit_message_text(
        msg,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


# =========================
# تست خبر - جمع‌آوری و نمایش واقعی
# =========================
async def send_test_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.message.reply_text("⏳ در حال جمع‌آوری اخبار از منابع...")
    
    try:
        # جمع‌آوری اخبار واقعی
        all_news = fetch_all_news()
        
        if not all_news:
            await query.message.reply_text("❌ هیچ خبر جدیدی یافت نشد.")
            return
        
        # رتبه‌بندی
        min_importance = int(get_setting("min_importance", "1"))
        ranked = rank_news(all_news, min_importance=min_importance)
        
        if not ranked:
            await query.message.reply_text(f"❌ هیچ خبری با اهمیت حداقل {min_importance} پیدا نشد.")
            return
        
        await query.message.reply_text(f"✅ {len(ranked)} خبر پیدا شد. ارسال 3 خبر اول...")
        
        # ارسال 3 خبر اول
        for item in ranked[:3]:
            # ترجمه
            title_fa = translate_title(item['title'])
            summary_fa = translate_title(item.get('summary', '')[:300]) if item.get('summary') else ""
            
            # دسته‌بندی
            category = classify_category(item['title'], item.get('summary', ''))
            category_hashtag = category.split()[1] if ' ' in category else category
            category_hashtag = f"#{category_hashtag}"
            
            # ایموجی اهمیت
            importance_emoji = {
                3: "🔥🔥🔥",
                2: "⭐⭐",
                1: "⭐",
                0: "•"
            }.get(item.get('importance', 1), "⭐")
            
            # ساخت پیام
            msg = (
                f"{category} {category_hashtag}\n\n"
                f"*{title_fa}*\n\n"
                f"{summary_fa}\n\n"
                f"🔗 [خبر اصلی]({item['link']})\n"
                f"{importance_emoji} اهمیت: {item.get('importance', 1)}/3"
            )
            
            await query.message.reply_text(
                msg,
                parse_mode="Markdown",
                disable_web_page_preview=False
            )
            
            await asyncio.sleep(1)  # تاخیر کوتاه
        
        await query.message.reply_text("✅ تست خبر کامل شد!")
        
    except Exception as e:
        await query.message.reply_text(f"❌ خطا در جمع‌آوری اخبار: {str(e)}")


# =========================
# تست ترند - محاسبه و نمایش واقعی
# =========================
async def send_test_trends(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.message.reply_text("⏳ در حال تحلیل ترندها...")
    
    try:
        # جمع‌آوری اخبار
        all_news = fetch_all_news()
        
        if not all_news:
            await query.message.reply_text("❌ هیچ خبری برای تحلیل ترند وجود ندارد.")
            return
        
        # پیدا کردن ترندها
        min_sources = int(get_setting("min_trend_sources", "2"))
        trends = find_daily_trends(all_news, min_sources=min_sources)
        
        if not trends:
            # اگر ترند پیدا نشد، خلاصه کلی بده
            summary = generate_daily_trend(all_news)
            await query.message.reply_text(
                f"📊 *تحلیل اخبار امروز*\n\n{summary}",
                parse_mode="Markdown"
            )
        else:
            # فرمت و ارسال ترندها
            trend_msg = format_trends_message(trends)
            await query.message.reply_text(
                trend_msg,
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
        
        await query.message.reply_text("✅ تست ترند کامل شد!")
        
    except Exception as e:
        await query.message.reply_text(f"❌ خطا در تحلیل ترند: {str(e)}")


# =========================
# افزودن RSS
# =========================
async def handle_add_rss(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_states[ADMIN_ID] = "waiting_rss"
    
    await query.message.reply_text(
        "📰 لطفاً آدرس RSS را ارسال کنید:\n"
        "مثال: https://site.com/feed\n\n"
        "برای لغو /cancel بزنید"
    )


# =========================
# افزودن Scraping
# =========================
async def handle_add_scrape(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_states[ADMIN_ID] = "waiting_scrape"
    
    await query.message.reply_text(
        "🕷️ لطفاً آدرس صفحه را ارسال کنید:\n"
        "مثال: https://site.com/news\n\n"
        "برای لغو /cancel بزنید"
    )


# =========================
# حذف منبع
# =========================
async def handle_remove_source(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_states[ADMIN_ID] = "waiting_remove"
    
    await query.message.reply_text(
        "❌ لطفاً آدرس منبعی که می‌خواهید حذف کنید را ارسال کنید:\n\n"
        "برای لغو /cancel بزنید"
    )


# =========================
# تنظیم کانال مقصد
# =========================
async def handle_set_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_states[ADMIN_ID] = "waiting_target"
    
    await query.message.reply_text(
        "🎯 لطفاً آیدی عددی کانال/گروه را ارسال کنید:\n"
        "مثال: -1001234567890\n\n"
        "💡 نکته: ربات باید admin کانال باشد\n"
        "برای لغو /cancel بزنید"
    )


# =========================
# تنظیم حداقل اهمیت
# =========================
async def handle_set_min_importance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_states[ADMIN_ID] = "waiting_importance"
    
    current = get_setting("min_importance", "1")
    
    await query.message.reply_text(
        f"⚙️ حداقل اهمیت فعلی: *{current}*\n\n"
        "عدد جدید را ارسال کنید (0 تا 3):\n"
        "• 0: همه اخبار\n"
        "• 1: اخبار معمولی\n"
        "• 2: اخبار مهم\n"
        "• 3: اخبار فوری\n\n"
        "برای لغو /cancel بزنید",
        parse_mode="Markdown"
    )


# =========================
# مدیریت کلمات کلیدی
# =========================
async def handle_manage_keywords(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    rules = get_all_rules()
    
    msg = "🔧 *مدیریت کلمات کلیدی اهمیت*\n\n"
    
    for level in sorted(rules.keys(), key=lambda x: int(x), reverse=True):
        data = rules[level]
        msg += f"⭐ *سطح {level} ({data['name']}):*\n"
        keywords = data.get('keywords', [])
        if keywords:
            msg += f"   {len(keywords)} کلمه: {', '.join(keywords[:5])}"
            if len(keywords) > 5:
                msg += f" و {len(keywords)-5} کلمه دیگر"
        else:
            msg += "   هیچ کلمه‌ای تنظیم نشده"
        msg += "\n\n"
    
    keyboard = [
        [InlineKeyboardButton("➕ افزودن کلمه", callback_data="add_keyword")],
        [InlineKeyboardButton("❌ حذف کلمه", callback_data="remove_keyword")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")]
    ]
    
    await query.edit_message_text(
        msg,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


# =========================
# تنظیمات زمان‌بندی
# =========================
async def handle_scheduling_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    fetch_interval = get_setting("news_fetch_interval_hours", "3")
    trend_hour = get_setting("trend_hour", "23")
    trend_minute = get_setting("trend_minute", "55")
    min_trend_sources = get_setting("min_trend_sources", "2")
    
    msg = "⏰ *تنظیمات زمان‌بندی*\n\n"
    msg += f"📰 بازه جمع‌آوری اخبار: هر {fetch_interval} ساعت\n"
    msg += f"📊 زمان ارسال ترند: {trend_hour}:{trend_minute}\n"
    msg += f"🔢 حداقل منابع برای ترند: {min_trend_sources}\n\n"
    msg += "برای تغییر هر کدام روی دکمه مربوطه کلیک کنید:"
    
    keyboard = [
        [InlineKeyboardButton("⏱️ تغییر بازه جمع‌آوری", callback_data="change_fetch_interval")],
        [InlineKeyboardButton("🕐 تغییر زمان ترند", callback_data="change_trend_time")],
        [InlineKeyboardButton("🔢 حداقل منابع ترند", callback_data="change_min_trend_sources")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")]
    ]
    
    await query.edit_message_text(
        msg,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


# =========================
# دریافت پیام از کاربر
# =========================
async def receive_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return
    
    text = update.message.text
    user_id = update.effective_user.id
    state = user_states.get(user_id)
    
    # لغو عملیات
    if text == "/cancel":
        user_states.pop(user_id, None)
        await update.message.reply_text("❌ عملیات لغو شد.")
        keyboard = get_main_menu_keyboard()
        await update.message.reply_text(
            "🎬 پنل مدیریت",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    # افزودن RSS
    if state == "waiting_rss":
        if text.startswith("http"):
            add_rss_source(text)
            await update.message.reply_text(f"✅ RSS اضافه شد:\n`{text}`", parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ آدرس نامعتبر است.")
        user_states.pop(user_id, None)
    
    # افزودن Scraping
    elif state == "waiting_scrape":
        if text.startswith("http"):
            add_scrape_source(text)
            await update.message.reply_text(f"✅ Scraping اضافه شد:\n`{text}`", parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ آدرس نامعتبر است.")
        user_states.pop(user_id, None)
    
    # حذف منبع
    elif state == "waiting_remove":
        if text in get_rss_sources():
            remove_rss_source(text)
            await update.message.reply_text("✅ RSS حذف شد.")
        elif text in get_scrape_sources():
            remove_scrape_source(text)
            await update.message.reply_text("✅ Scraping حذف شد.")
        else:
            await update.message.reply_text("❌ منبع یافت نشد.")
        user_states.pop(user_id, None)
    
    # تنظیم کانال مقصد
    elif state == "waiting_target":
        try:
            chat_id = int(text)
            set_setting("TARGET_CHAT_ID", str(chat_id))
            await update.message.reply_text(f"✅ کانال مقصد تنظیم شد: `{chat_id}`", parse_mode="Markdown")
            
            # تست ارسال
            try:
                from telegram import Bot
                bot = Bot(token=os.getenv("BOT_TOKEN"))
                await bot.send_message(
                    chat_id=chat_id,
                    text="✅ ربات با موفقیت به کانال متصل شد!"
                )
                await update.message.reply_text("✅ پیام تست ارسال شد!")
            except Exception as e:
                await update.message.reply_text(f"⚠️ کانال تنظیم شد ولی ارسال تست ناموفق بود:\n{str(e)}")
        except:
            await update.message.reply_text("❌ آیدی نامعتبر است.")
        user_states.pop(user_id, None)
    
    # تنظیم اهمیت
    elif state == "waiting_importance":
        try:
            level = int(text)
            if 0 <= level <= 3:
                set_setting("min_importance", str(level))
                await update.message.reply_text(f"✅ حداقل اهمیت به {level} تغییر کرد.")
            else:
                await update.message.reply_text("❌ عدد باید بین 0 تا 3 باشد.")
        except:
            await update.message.reply_text("❌ عدد نامعتبر است.")
        user_states.pop(user_id, None)


# =========================
# Callback دکمه‌ها
# =========================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_admin(update):
        return

    data = query.data

    # منوی اصلی
    if data == "back_to_main":
        await show_main_menu(query)
    
    # وضعیت
    elif data == "status":
        await show_status(update, context)
    
    # لیست منابع
    elif data == "list_sources":
        await list_sources(update, context)
    
    # تست خبر
    elif data == "send_test_news":
        await send_test_news(update, context)
    
    # تست ترند
    elif data == "send_test_trends":
        await send_test_trends(update, context)
    
    # افزودن RSS
    elif data == "add_rss":
        await handle_add_rss(update, context)
    
    # افزودن Scraping
    elif data == "add_scrape":
        await handle_add_scrape(update, context)
    
    # حذف منبع
    elif data == "remove_source":
        await handle_remove_source(update, context)
    
    # تنظیم کانال
    elif data == "set_target":
        await handle_set_target(update, context)
    
    # تنظیم اهمیت
    elif data == "set_min_importance":
        await handle_set_min_importance(update, context)
    
    # مدیریت کلمات
    elif data == "manage_keywords":
        await handle_manage_keywords(update, context)
    
    # تنظیمات زمان‌بندی
    elif data == "scheduling_settings":
        await handle_scheduling_settings(update, context)


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
