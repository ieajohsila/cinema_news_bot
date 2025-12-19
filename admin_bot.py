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
        await update.message.reply_text("⛔️ شما دسترسی به این ربات ندارید.")
        return

    keyboard = [
        [InlineKeyboardButton("📋 نمایش منابع", callback_data="list_sources")],
        [InlineKeyboardButton("➕ افزودن RSS", callback_data="add_rss")],
        [InlineKeyboardButton("➕ افزودن Scraping", callback_data="add_scrape")],
        [InlineKeyboardButton("❌ حذف منبع", callback_data="remove_source")],
        [InlineKeyboardButton("🎯 تنظیم کانال مقصد", callback_data="set_target")],
        [InlineKeyboardButton("⚙️ تنظیم حداقل اهمیت", callback_data="set_min_importance")],
        [InlineKeyboardButton("🔧 مدیریت کلمات کلیدی", callback_data="manage_keywords")],
    ]

    await update.message.reply_text(
        "🎬 پنل مدیریت ربات خبری سینما:",
        reply_markup=InlineKeyboardMarkup(keyboard),
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
    
    await update.message.reply_text(msg, parse_mode="Markdown")


# =========================
# مدیریت کلمات کلیدی
# =========================
async def manage_keywords_menu(message):
    """منوی مدیریت کلمات کلیدی"""
    rules = get_all_rules()
    
    keyboard = []
    for level in sorted(rules.keys(), key=lambda x: int(x), reverse=True):
        level_data = rules[level]
        keyboard.append([
            InlineKeyboardButton(
                f"⭐ سطح {level} ({level_data['name']}) - {len(level_data['keywords'])} کلمه",
                callback_data=f"keywords_level|{level}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("➕ افزودن سطح جدید", callback_data="add_new_level")])
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")])
    
    await message.reply_text(
        "🔧 *مدیریت کلمات کلیدی اهمیت*\n\n"
        "روی هر سطح کلیک کنید تا کلمات آن را ببینید:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def show_level_keywords(query, level):
    """نمایش کلمات یک سطح خاص"""
    rules = get_all_rules()
    level_data = rules.get(str(level), {})
    keywords = level_data.get("keywords", [])
    
    msg = f"⭐ *سطح {level} - {level_data.get('name', 'نامشخص')}*\n\n"
    msg += f"📝 تعداد کلمات: {len(keywords)}\n\n"
    
    if keywords:
        msg += "*کلمات کلیدی:*\n"
        for i, kw in enumerate(keywords, 1):
            msg += f"{i}. {kw}\n"
    else:
        msg += "هیچ کلمه‌ای تعریف نشده است."
    
    keyboard = [
        [InlineKeyboardButton("➕ افزودن کلمه", callback_data=f"add_keyword|{level}")],
        [InlineKeyboardButton("➖ حذف کلمه", callback_data=f"remove_keyword|{level}")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="manage_keywords")]
    ]
    
    await query.edit_message_text(
        msg,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


# =========================
# Callback دکمه‌ها
# =========================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_admin(update):
        return

    data = query.data

    if data == "add_rss":
        context.user_data.clear()
        context.user_data["awaiting_add_rss"] = True
        await query.message.reply_text("📰 آدرس RSS را ارسال کنید:")

    elif data == "add_scrape":
        context.user_data.clear()
        context.user_data["awaiting_add_scrape"] = True
        await query.message.reply_text("🕷️ آدرس سایت Scraping را ارسال کنید:")

    elif data == "remove_source":
        await show_remove_source_menu(query.message)

    elif data == "list_sources":
        await list_sources(query, context)

    elif data == "set_target":
        context.user_data.clear()
        context.user_data["awaiting_target"] = True
        await query.message.reply_text(
            "🎯 آیدی عددی گروه یا کانال مقصد را ارسال کنید\n"
            "(مثلاً: -1001234567890):"
        )

    elif data == "set_min_importance":
        context.user_data.clear()
        context.user_data["awaiting_min_importance"] = True
        await query.message.reply_text(
            "⚙️ حداقل سطح اهمیت ارسال خبر را وارد کنید (0 تا 3):\n\n"
            "0 = همه اخبار\n"
            "1 = معمولی و بالاتر\n"
            "2 = مهم و فوری\n"
            "3 = فقط فوری"
        )

    elif data == "manage_keywords":
        await manage_keywords_menu(query.message)

    elif data.startswith("keywords_level|"):
        level = data.split("|")[1]
        await show_level_keywords(query, level)

    elif data.startswith("add_keyword|"):
        level = data.split("|")[1]
        context.user_data.clear()
        context.user_data["awaiting_add_keyword"] = True
        context.user_data["keyword_level"] = level
        await query.message.reply_text(
            f"➕ کلمه جدید برای سطح {level} را ارسال کنید:\n\n"
            "نکته: می‌توانید چند کلمه را با ویرگول جدا کنید\n"
            "مثال: جشنواره, برلین, ونیز"
        )

    elif data.startswith("remove_keyword|"):
        level = data.split("|")[1]
        keywords = get_level_keywords(int(level))
        
        if not keywords:
            await query.message.reply_text("❌ هیچ کلمه‌ای برای حذف وجود ندارد.")
            return
        
        keyboard = []
        for kw in keywords:
            keyboard.append([
                InlineKeyboardButton(
                    f"❌ {kw}",
                    callback_data=f"del_keyword|{level}|{kw}"
                )
            ])
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data=f"keywords_level|{level}")])
        
        await query.message.reply_text(
            f"➖ کلمه موردنظر برای حذف از سطح {level} را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data.startswith("del_keyword|"):
        parts = data.split("|")
        level = parts[1]
        keyword = parts[2]
        
        if remove_keyword(int(level), keyword):
            await query.answer(f"✅ کلمه '{keyword}' حذف شد")
            await show_level_keywords(query, level)
        else:
            await query.answer("❌ خطا در حذف کلمه")

    elif data == "add_new_level":
        context.user_data.clear()
        context.user_data["awaiting_new_level"] = True
        await query.message.reply_text(
            "➕ *افزودن سطح جدید*\n\n"
            "لطفاً شماره سطح را ارسال کنید (مثلاً: 4 یا 5):",
            parse_mode="Markdown"
        )

    elif data == "back_to_main":
        await start(query, context)


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
        await message.reply_text(
            "❌ هیچ منبعی برای حذف وجود ندارد.\n\n"
            "💡 برای افزودن منبع از دکمه‌های پنل اصلی استفاده کنید."
        )
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

    # تنظیم حداقل اهمیت
    if context.user_data.get("awaiting_min_importance"):
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

    # افزودن کلمه کلیدی
    if context.user_data.get("awaiting_add_keyword"):
        level = int(context.user_data["keyword_level"])
        
        # پردازش چند کلمه با ویرگول
        keywords = [kw.strip() for kw in text.split(",")]
        added = 0
        
        for kw in keywords:
            if kw and add_keyword(level, kw):
                added += 1
        
        context.user_data.clear()
        await update.message.reply_text(
            f"✅ {added} کلمه به سطح {level} اضافه شد:\n" + ", ".join(keywords)
        )
        return

    # افزودن سطح جدید
    if context.user_data.get("awaiting_new_level"):
        try:
            level = int(text)
            if 0 <= level <= 10:
                context.user_data["new_level_number"] = level
                context.user_data["awaiting_new_level"] = False
                context.user_data["awaiting_new_level_name"] = True
                await update.message.reply_text(
                    f"✅ سطح {level} را انتخاب کردید.\n\n"
                    f"حالا یک نام فارسی برای این سطح ارسال کنید:"
                )
            else:
                await update.message.reply_text("❌ شماره سطح باید بین 0 تا 10 باشد.")
        except ValueError:
            await update.message.reply_text("❌ لطفاً یک عدد صحیح ارسال کنید.")
        return

    # نام سطح جدید
    if context.user_data.get("awaiting_new_level_name"):
        level = context.user_data["new_level_number"]
        name = text
        add_new_level(level, name, [])
        context.user_data.clear()
        await update.message.reply_text(
            f"✅ سطح {level} ({name}) با موفقیت اضافه شد.\n\n"
            f"حالا می‌توانید از منوی مدیریت کلمات کلیدی، کلمه به آن اضافه کنید."
        )
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
    application.add_handler(CommandHandler("sources", list_sources))
    application.add_handler(CallbackQueryHandler(remove_source_callback, pattern=r"^del_(rss|scrape)\|"))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_message))

    return application


# برای import کردن در main.py
app = create_app()


# =========================
# اجرای مستقیم
# =========================
if __name__ == "__main__":
    print("🤖 ربات خبری سینما در حال راه‌اندازی...")
    print("✅ ربات آماده است و منتظر دریافت پیام...")
    app.run_polling()
