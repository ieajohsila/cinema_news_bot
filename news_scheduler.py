"""
🔧 FIX برای news_scheduler.py

جایگزین کردن قسمت ارسال اخبار (حدود خط 85 تا 125)
"""

# قسمت قبلی (حدود خط 85)
async def fetch_and_send_news():
    """هر N ساعت یکبار اخبار جدید را جمع‌آوری و رتبه‌بندی و ارسال می‌کند."""
    logger.info("\n" + "="*60)
    logger.info("⏰ شروع جمع‌آوری اخبار...")
    logger.info(f"🕐 زمان تهران: {now_tehran().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*60)
    
    # ... کد جمع‌آوری و رتبه‌بندی ...
    
    logger.info(f"📨 در حال ارسال {len(ranked)} خبر به کانال {TARGET_CHAT_ID}...")

    sent_count = 0
    today = now_tehran().date().isoformat()
    
    # import برای ذخیره ترند
    from database import save_topic
    
    for item in ranked:
        # ✅ ترجمه با مدیریت کامل خطا
        try:
            title_fa = translate_title(item['title'])
            # چک کردن نتیجه
            if not title_fa or not isinstance(title_fa, str) or len(title_fa.strip()) == 0:
                logger.warning(f"⚠️ ترجمه عنوان خالی بود، استفاده از متن اصلی")
                title_fa = item['title']
        except Exception as e:
            logger.warning(f"⚠️ خطا در ترجمه عنوان: {type(e).__name__}: {str(e)[:100]}")
            title_fa = item['title']
        
        # ترجمه خلاصه
        summary_fa = ""
        try:
            if item.get('summary'):
                summary_text = item['summary'][:300]
                summary_fa = translate_title(summary_text)
                # چک کردن نتیجه
                if not summary_fa or not isinstance(summary_fa, str) or len(summary_fa.strip()) == 0:
                    logger.warning(f"⚠️ ترجمه خلاصه خالی بود، استفاده از متن اصلی")
                    summary_fa = summary_text
        except Exception as e:
            logger.warning(f"⚠️ خطا در ترجمه خلاصه: {type(e).__name__}: {str(e)[:100]}")
            summary_fa = item.get('summary', '')[:300] if item.get('summary') else ""
        
        # دسته‌بندی
        try:
            category = classify_category(item['title'], item.get('summary', ''))
        except Exception as e:
            logger.warning(f"⚠️ خطا در دسته‌بندی: {e}")
            category = "🎬 فیلم"
        
        # تبدیل دسته به هشتگ قابل جستجو
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
        
        try:
            await bot.send_message(
                chat_id=TARGET_CHAT_ID,
                text=msg,
                parse_mode="Markdown",
                disable_web_page_preview=False,
            )
            sent_count += 1
            
            # ذخیره برای ترند
            try:
                save_topic(
                    topic=item['title'],
                    link=item['link'],
                    source=item.get('source', 'unknown'),
                    date=today
                )
            except Exception as e:
                logger.warning(f"⚠️ خطا در ذخیره topic: {e}")
            
            logger.info(f"✅ ارسال شد: {title_fa[:40]}...")
            await asyncio.sleep(3)  # تاخیر برای جلوگیری از Flood
            
        except RetryAfter as e:
            logger.warning(f"⏱️  Flood control: صبر {e.retry_after} ثانیه...")
            await asyncio.sleep(e.retry_after + 1)
            
            # تلاش مجدد
            try:
                await bot.send_message(
                    chat_id=TARGET_CHAT_ID,
                    text=msg,
                    parse_mode="Markdown",
                    disable_web_page_preview=False,
                )
                sent_count += 1
                try:
                    save_topic(
                        topic=item['title'],
                        link=item['link'],
                        source=item.get('source', 'unknown'),
                        date=today
                    )
                except:
                    pass
                logger.info(f"✅ ارسال شد (تلاش دوم): {title_fa[:40]}...")
            except Exception as e2:
                logger.error(f"❌ خطا در تلاش دوم: {e2}")
                
        except TelegramError as e:
            logger.error(f"❌ خطا در ارسال خبر: {e}")
        except Exception as e:
            logger.error(f"❌ خطای غیرمنتظره در ارسال: {type(e).__name__}: {e}")

    logger.info(f"✅ {sent_count} خبر با موفقیت ارسال شد.")
    
    # ذخیره زمان ارسال
    set_setting("last_news_send", now_tehran().isoformat())
    logger.info("="*60 + "\n")
