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
    get_collected_news,
    save_collected_news,
    daily_trends,
)
from importance import (
    get_all_rules,
    get_level_keywords,
    add_keyword,
    remove_keyword,
    add_new_level,
)
from status_handler import get_status_message
from news_fetcher import fetch_all_news
from news_ranker import rank_news
from translation import translate_title
from category import classify_category
from datetime import datetime

ADMIN_ID = 81155585  # آیدی ادمین

# حالت‌های ورودی
USER_STATE = {}

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
        [InlineKeyboardButton("📰 تست خبر واقعی", callback_data="send_test_news")],
        [InlineKeyboardButton("📈 تست ترند واقعی", callback_data="send_test_trends")],
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
    
    rss = get_rss_sources()
    scrape = get_scrape_sources()
    
    msg = "📋 *منابع فعال*\n\n"
    
    msg += f"📰 *RSS ({len(rss)} منبع):*\n"
    for i, url in enumerate(rss, 1):
        msg += f"{i}. `{url}`\n"
    
    msg += f"\n🕷️ *Scraping ({len(scrape)} منبع):*\n"
    for i, url in enumerate(scrape, 1):
        msg += f"{i}. `{url}`\n"
    
    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")]]
    
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

# =========================
# تست خبر واقعی
# =========================
async def send_test_news(query):
    """جمع‌آوری اخبار جدید و نمایش یکی از آنها"""
    await query.answer("⏳ در حال جمع‌آوری اخبار...")
    
    try:
        # جمع‌آوری اخبار
        await query.message.reply_text("🔄 در حال جمع‌آوری اخبار از منابع...")
        all_news = fetch_all_news()
        
        if not all_news:
            await query.message.reply_text("❌ هیچ خبری یافت نشد.")
            return
        
        # رتبه‌بندی
        min_importance = int(get_setting("min_importance", 1))
        ranked = rank_news(all_news, min_importance=min_importance)
        
        if not ranked:
            await query.message.reply_text(f"❌ هیچ خبری با اهمیت حداقل {min_importance} پیدا نشد.")
            return
        
        # ذخیره اخبار
        save_collected_news(ranked)
        
        # نمایش اولین خبر
        n = ranked[0]
        
        # ترجمه
        title_fa = translate_title(n['title'])
        summary_fa = translate_title(n.get('summary', '')[:300]) if n.get('summary') else ""
        
        # دسته‌بندی
        category = classify_category(n['title'], n.get('summary', ''))
        
        # ایموجی اهمیت
        importance_emoji = {
            3: "🔥🔥🔥",
            2: "⭐⭐",
            1: "⭐",
            0: "•"
        }.get(n.get('importance', 1), "⭐")
        
        msg = f"📰 *خبر تست واقعی*\n\n"
        msg += f"🏷️ دسته: {category}\n\n"
        msg += f"*{title_fa}*\n\n"
        if summary_fa:
            msg += f"{summary_fa}\n\n"
        msg += f"🔗 [مشاهده خبر]({n['link']})\n"
        msg += f"{importance_emoji} اهمیت: {n.get('importance', 1)}/3\n\n"
        msg += f"✅ جمعاً {len(ranked)} خبر جمع‌آوری شد"

        await query.message.reply_text(msg, parse_mode="Markdown", disable_web_page_preview=False)
        
    except Exception as e:
        await query.message.reply_text(f"❌ خطا: {str(e)}")


# =========================
# تست ترند واقعی
# =========================
async def send_test_trends(query):
    """محاسبه و نمایش ترندهای واقعی از اخبار امروز"""
    await query.answer("⏳ در حال تحلیل ترندها...")
    
    try:
        # دریافت اخبار امروز
        today = datetime.utcnow().date().isoformat()
        trends = daily_trends(today)
        
        if not trends:
            await query.message.reply_text("❌ هیچ ترندی امروز شناسایی نشد.\n\n💡 ترند = خبری که از 2 منبع یا بیشتر آمده باشد")
            return
        
        msg = "📈 *ترندهای امروز سینما*\n\n"
        msg += f"📅 {today}\n\n"
        
        for i, trend in enumerate(trends[:10], 1):
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}️⃣"
            
            msg += f"{emoji} *{trend['topic'][:80]}*\n"
            msg += f"   📰 منابع: {', '.join(trend['sources'][:3])}\n"
            
            if len(trend['sources']) > 3:
                msg += f"   ➕ و {len(trend['sources']) - 3} منبع دیگر\n"
            
            if trend['links'] and trend['links'][0]:
                msg += f"   🔗 [مشاهده]({trend['links'][0]})\n"
            
            msg += "\n"
        
        msg += f"━━━━━━━━━━━━━━━━━\n"
        msg += f"🔥 {len(trends)} ترند فعال"

        await query.message.reply_text(msg, parse_mode="Markdown", disable_web_page_preview=True)
        
    except Exception as e:
        await query.message.reply_text(f"❌ خطا: {str(e)}")


# =========================
# تنظیم کانال مقصد
# =========================
async def set_target_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    USER_STATE[ADMIN_ID] = "waiting_target"
    
    msg = "🎯 *تنظیم کانال مقصد*\n\n"
    msg += "لطفاً Chat ID کانال یا گروه خود را ارسال کنید.\n\n"
    msg += "💡 برای دریافت Chat ID:\n"
    msg += "1. ربات را به کانال اضافه کنید\n"
    msg += "2. از @userinfobot استفاده کنید\n\n"
    msg += "مثال: `-1001234567890`"
    
    keyboard = [[InlineKeyboardButton("❌ لغو", callback_data="back_to_main")]]
    
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


# =========================
# تنظیم حداقل اهمیت
# =========================
async def set_min_importance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    USER_STATE[ADMIN_ID] = "waiting_importance"
    
    msg = "⚙️ *تنظیم حداقل اهمیت*\n\n"
    msg += "سطح اهمیت را وارد کنید (0 تا 3):\n\n"
    msg += "0️⃣ کم‌اهمیت (rumor, speculation)\n"
    msg += "1️⃣ معمولی (review, interview)\n"
    msg += "2️⃣ مهم (trailer, box office)\n"
    msg += "3️⃣ فوری (breaking, Oscar)\n\n"
    msg += f"📊 سطح فعلی: {get_setting('min_importance', '1')}"
    
    keyboard = [[InlineKeyboardButton("❌ لغو", callback_data="back_to_main")]]
    
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


# =========================
# افزودن RSS
# =========================
async def add_rss_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    USER_STATE[ADMIN_ID] = "waiting_rss"
    
    msg = "➕ *افزودن منبع RSS*\n\n"
    msg += "لطفاً URL فید RSS را ارسال کنید.\n\n"
    msg += "مثال:\n`https://variety.com/feed/`"
    
    keyboard = [[InlineKeyboardButton("❌ لغو", callback_data="back_to_main")]]
    
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


# =========================
# افزودن Scrape
# =========================
async def add_scrape_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    USER_STATE[ADMIN_ID] = "waiting_scrape"
    
    msg = "➕ *افزودن منبع Scraping*\n\n"
    msg += "لطفاً URL صفحه خبری را ارسال کنید.\n\n"
    msg += "مثال:\n`https://www.hollywoodreporter.com/news/`"
    
    keyboard = [[InlineKeyboardButton("❌ لغو", callback_data="back_to_main")]]
    
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


# =========================
# حذف منبع
# =========================
async def remove_source_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    rss = get_rss_sources()
    scrape = get_scrape_sources()
    
    if not rss and not scrape:
        await query.message.reply_text("❌ هیچ منبعی برای حذف وجود ندارد.")
        return
    
    keyboard = []
    
    for url in rss:
        keyboard.append([InlineKeyboardButton(f"❌ {url[:50]}", callback_data=f"remove_rss:{url}")])
    
    for url in scrape:
        keyboard.append([InlineKeyboardButton(f"❌ {url[:50]}", callback_data=f"remove_scrape:{url}")])
    
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")])
    
    try:
        await query.edit_message_text(
            "❌ *حذف منبع*\n\nروی منبع مورد نظر کلیک کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    except:
        await query.message.reply_text(
            "❌ *حذف منبع*\n\nروی منبع مورد نظر کلیک کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )


# =========================
# مدیریت کلمات کلیدی
# =========================
async def manage_keywords_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    rules = get_all_rules()
    
    msg = "🔧 *مدیریت کلمات کلیدی*\n\n"
    
    for level in sorted(rules.keys(), key=lambda x: int(x)):
        rule = rules[level]
        msg += f"*سطح {level} ({rule['name']}):*\n"
        msg += f"تعداد کلمات: {len(rule['keywords'])}\n\n"
    
    keyboard = [
        [InlineKeyboardButton("➕ افزودن کلمه", callback_data="add_keyword")],
        [InlineKeyboardButton("❌ حذف کلمه", callback_data="remove_keyword")],
        [InlineKeyboardButton("📋 نمایش کلمات", callback_data="show_keywords")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")]
    ]
    
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


# =========================
# تنظیمات زمان‌بندی
# =========================
async def scheduling_settings_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    fetch_interval = get_setting("news_fetch_interval_hours", "3")
    trend_hour = get_setting("trend_hour", "23")
    trend_minute = get_setting("trend_minute", "55")
    
    msg = "⏰ *تنظیمات زمان‌بندی*\n\n"
    msg += f"📰 بازه جمع‌آوری اخبار: هر {fetch_interval} ساعت\n"
    msg += f"📊 ارسال ترند روزانه: {trend_hour}:{trend_minute}\n\n"
    msg += "برای تغییر تنظیمات، یکی از دکمه‌ها را انتخاب کنید:"
    
    keyboard = [
        [InlineKeyboardButton("⏱️ تغییر بازه اخبار", callback_data="change_fetch_interval")],
        [InlineKeyboardButton("🕐 تغییر زمان ترند", callback_data="change_trend_time")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")]
    ]
    
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


# =========================
# دریافت پیام‌های متنی
# =========================
async def receive_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return
    
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    state = USER_STATE.get(user_id)
    
    if state == "waiting_target":
        try:
            chat_id = int(text)
            set_setting("TARGET_CHAT_ID", str(chat_id))
            
            # تست ارسال
            try:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="✅ کانال مقصد با موفقیت تنظیم شد!"
                )
                await update.message.reply_text(
                    f"✅ کانال مقصد تنظیم شد: `{chat_id}`",
                    parse_mode="Markdown"
                )
            except Exception as e:
                await update.message.reply_text(
                    f"⚠️ Chat ID ذخیره شد اما ارسال تست ناموفق بود.\n\n"
                    f"خطا: {str(e)}\n\n"
                    f"💡 مطمئن شوید ربات Admin کانال است."
                )
            
            USER_STATE.pop(user_id, None)
            
        except ValueError:
            await update.message.reply_text("❌ Chat ID باید عدد باشد. دوباره تلاش کنید:")
    
    elif state == "waiting_importance":
        try:
            level = int(text)
            if 0 <= level <= 3:
                set_setting("min_importance", str(level))
                await update.message.reply_text(f"✅ حداقل اهمیت به {level} تنظیم شد.")
                USER_STATE.pop(user_id, None)
            else:
                await update.message.reply_text("❌ عدد باید بین 0 تا 3 باشد:")
        except ValueError:
            await update.message.reply_text("❌ لطفاً یک عدد وارد کنید:")
    
    elif state == "waiting_rss":
        if text.startswith("http"):
            add_rss_source(text)
            await update.message.reply_text(f"✅ منبع RSS اضافه شد:\n`{text}`", parse_mode="Markdown")
            USER_STATE.pop(user_id, None)
        else:
            await update.message.reply_text("❌ URL باید با http شروع شود:")
    
    elif state == "waiting_scrape":
        if text.startswith("http"):
            add_scrape_source(text)
            await update.message.reply_text(f"✅ منبع Scraping اضافه شد:\n`{text}`", parse_mode="Markdown")
            USER_STATE.pop(user_id, None)
        else:
            await update.message.reply_text("❌ URL باید با http شروع شود:")


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
        USER_STATE.pop(ADMIN_ID, None)
        await show_main_menu(query)
    
    elif data == "status":
        await show_status(update, context)
    
    elif data == "list_sources":
        await list_sources(update, context)
    
    elif data == "send_test_news":
        await send_test_news(query)
    
    elif data == "send_test_trends":
        await send_test_trends(query)
    
    elif data == "set_target":
        await set_target_channel(update, context)
    
    elif data == "set_min_importance":
        await set_min_importance(update, context)
    
    elif data == "add_rss":
        await add_rss_handler(update, context)
    
    elif data == "add_scrape":
        await add_scrape_handler(update, context)
    
    elif data == "remove_source":
        await remove_source_handler(update, context)
    
    elif data == "manage_keywords":
        await manage_keywords_handler(update, context)
    
    elif data == "scheduling_settings":
        await scheduling_settings_handler(update, context)
    
    elif data.startswith("remove_rss:"):
        url = data.replace("remove_rss:", "")
        remove_rss_source(url)
        await query.message.reply_text(f"✅ منبع RSS حذف شد:\n`{url}`", parse_mode="Markdown")
        await show_main_menu(query)
    
    elif data.startswith("remove_scrape:"):
        url = data.replace("remove_scrape:", "")
        remove_scrape_source(url)
        await query.message.reply_text(f"✅ منبع Scraping حذف شد:\n`{url}`", parse_mode="Markdown")
        await show_main_menu(query)


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
