# admin_bot.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from database import set_setting, get_setting

ADMIN_ID = 81155585  # آیدی عددی شما

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

# مدیریت اهمیت اخبار
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
            await update.message.reply_text(
                f"حداقل سطح اهمیت روی {val} تنظیم شد."
            )
        context.user_data["awaiting_importance"] = False

# تنظیم گروه/کانال مقصد
async def set_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "لطفاً آیدی عددی گروه یا کانال مقصد را ارسال کنید (مثلاً: -1001234567890):"
    )
    context.user_data["awaiting_target"] = True

async def receive_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_target"):
        val = update.message.text.strip()
        set_setting("TARGET_CHAT_ID", val)
        await update.message.reply_text(f"گروه/کانال مقصد روی {val} تنظیم شد.")
        context.user_data["awaiting_target"] = False

# ایجاد اپلیکیشن و هَندلرها
if __name__ == "__main__":
    app = ApplicationBuilder().token("BOT_TOKEN").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("set_importance", set_importance))
    app.add_handler(CommandHandler("set_target", set_target))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_importance))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_target))

    app.run_polling()

