import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    CallbackQueryHandler, MessageHandler, filters, ContextTypes
)
from database import (
    add_source, remove_source, get_sources,
    set_setting
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    kb = [
        [InlineKeyboardButton("➕ افزودن RSS", callback_data="add_rss")],
        [InlineKeyboardButton("❌ حذف منبع", callback_data="remove")],
        [InlineKeyboardButton("🎯 تنظیم مقصد", callback_data="target")],
        [InlineKeyboardButton("⚙️ حداقل اهمیت", callback_data="importance")]
    ]
    await update.message.reply_text("پنل مدیریت:", reply_markup=InlineKeyboardMarkup(kb))

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data == "add_rss":
        context.user_data["await_rss"] = True
        await q.message.reply_text("لینک RSS را ارسال کنید:")

    elif q.data == "remove":
        sources = get_sources()
        kb = [[InlineKeyboardButton(s["url"], callback_data=f"rm_{i}")]
              for i, s in enumerate(sources)]
        await q.message.reply_text("منبع را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(kb))

    elif q.data == "target":
        context.user_data["await_target"] = True
        await q.message.reply_text("آیدی عددی گروه/کانال:")

    elif q.data == "importance":
        context.user_data["await_imp"] = True
        await q.message.reply_text("حداقل اهمیت (1-3):")

    elif q.data.startswith("rm_"):
        remove_source(int(q.data.split("_")[1]))
        await q.message.reply_text("منبع حذف شد.")

async def receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t = update.message.text.strip()

    if context.user_data.pop("await_rss", False):
        add_source({"type": "rss", "url": t})
        await update.message.reply_text("RSS اضافه شد.")

    elif context.user_data.pop("await_target", False):
        set_setting("TARGET_CHAT_ID", t)
        await update.message.reply_text("مقصد ذخیره شد. پیام تست ارسال می‌شود.")
        await update.get_bot().send_message(chat_id=t, text="✅ اتصال برقرار شد")

    elif context.user_data.pop("await_imp", False):
        set_setting("MIN_IMPORTANCE", int(t))
        await update.message.reply_text("حداقل اهمیت ذخیره شد.")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(menu))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive))

app.run_polling()
