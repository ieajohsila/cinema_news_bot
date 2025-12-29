"""
ماژول ترجمه و پردازش متن با Google Gemini
- ترجمه انگلیسی به فارسی
- fallback امن
- لاگ شفاف
- بدون system_instruction (سازگار با SDK فعلی)
"""

import os
import time
import logging
from typing import Optional, List
import google.generativeai as genai

# -------------------------------------------------
# Logger
# -------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------------------------------------
# Gemini Config
# -------------------------------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
model = None

logger.info("="*60)
logger.info("🔧 شروع مقداردهی سیستم ترجمه...")
logger.info("="*60)

if GEMINI_API_KEY:
    logger.info(f"✅ GEMINI_API_KEY یافت شد: {GEMINI_API_KEY[:20]}...")
    
    try:
        logger.info("⏳ در حال پیکربندی Gemini...")
        genai.configure(api_key=GEMINI_API_KEY)
        logger.info("✅ پیکربندی Gemini موفق")
        
        logger.info("⏳ در حال ساخت مدل gemini-1.5-flash...")
        model = genai.GenerativeModel("gemini-1.5-flash")
        logger.info("✅ مدل Gemini ساخته شد")
        
        # تست سریع
        logger.info("⏳ تست سریع ترجمه...")
        test_response = model.generate_content("Translate to Persian: Hello")
        if test_response and test_response.text:
            logger.info(f"✅ تست ترجمه موفق: {test_response.text[:50]}")
        else:
            logger.warning("⚠️ تست ترجمه پاسخ خالی داد")
            
    except Exception as e:
        logger.error(f"❌ خطا در مقداردهی Gemini: {e}", exc_info=True)
        logger.error(f"   نوع خطا: {type(e).__name__}")
        model = None
else:
    logger.warning("⚠️ GEMINI_API_KEY یافت نشد - ترجمه غیرفعال است")
    logger.warning("💡 برای فعال‌سازی، در Railway Variables تنظیم کنید:")
    logger.warning("   کلید: GEMINI_API_KEY")
    logger.warning("   مقدار: your-api-key-here")

logger.info("="*60)

# -------------------------------------------------
# Prompt Builder
# -------------------------------------------------
def build_translation_prompt(text: str) -> str:
    return f"""You are a professional English-to-Persian translator.

Rules:
- Translate the text into fluent, natural Persian.
- Preserve the original tone (formal or informal).
- DO NOT add explanations.
- DO NOT add labels or prefixes.
- Return ONLY the Persian translation.

Text:
{text}

Persian translation:
""".strip()


# -------------------------------------------------
# Core Translation
# -------------------------------------------------
def translate_to_persian(text: str, max_retries: int = 2) -> Optional[str]:
    if not model:
        logger.debug("❌ مدل Gemini در دسترس نیست")
        return None

    if not text or not text.strip():
        return None

    text = text.strip()

    if len(text) < 3:
        return None

    prompt = build_translation_prompt(text)

    logger.info(f"🌐 ترجمه: {text[:80]}...")

    for attempt in range(1, max_retries + 2):
        try:
            logger.debug(f"   تلاش {attempt} از {max_retries + 1}...")
            response = model.generate_content(prompt)

            if not response or not response.text:
                logger.warning(f"⚠️ پاسخ خالی (تلاش {attempt})")
                continue

            translated = response.text.strip()

            # پاکسازی خروجی‌های مزاحم احتمالی
            unwanted_prefixes = (
                "ترجمه:",
                "Translation:",
                "Persian translation:",
                "ترجمه فارسی:",
            )

            for prefix in unwanted_prefixes:
                if translated.startswith(prefix):
                    translated = translated[len(prefix):].strip()

            logger.info(f"✅ ترجمه موفق: {translated[:80]}...")
            return translated

        except Exception as e:
            logger.error(f"❌ خطا در ترجمه (تلاش {attempt}): {e}")
            logger.error(f"   نوع خطا: {type(e).__name__}")

            if attempt >= max_retries + 1:
                logger.error("❌ ترجمه کاملاً ناموفق بود")
                return None

            time.sleep(1)

    return None


# -------------------------------------------------
# Fallback Wrapper
# -------------------------------------------------
def translate_with_fallback(text: str) -> str:
    """ترجمه با fallback - اگر ترجمه نشد، متن اصلی برمی‌گرده"""
    
    # اگر مدل اصلاً نساخته شده، مستقیم متن اصلی رو برگردون
    if not model:
        logger.debug(f"⚠️ مدل غیرفعال - متن اصلی: {text[:50]}...")
        return text
    
    translated = translate_to_persian(text)

    if not translated:
        logger.warning(f"⚠️ ترجمه ناموفق - متن اصلی: {text[:50]}...")
        return text

    return translated


# -------------------------------------------------
# Backward Compatibility
# -------------------------------------------------
def translate_title(text: str) -> str:
    """تابع قدیمی برای سازگاری"""
    return translate_with_fallback(text)


# -------------------------------------------------
# Batch Translation
# -------------------------------------------------
def batch_translate(texts: List[str], delay: float = 0.5) -> List[str]:
    """ترجمه دسته‌ای"""
    results = []

    for text in texts:
        results.append(translate_with_fallback(text))

        if delay > 0:
            time.sleep(delay)

    return results


# -------------------------------------------------
# Manual Test
# -------------------------------------------------
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 تست دستی ترجمه")
    print("="*60)
    
    test_texts = [
        "Breaking: New Spielberg Movie Announced for 2025",
        "Christopher Nolan wins Best Director Oscar",
        "Marvel releases new trailer"
    ]
    
    for text in test_texts:
        print(f"\n📝 اصلی: {text}")
        translated = translate_to_persian(text)
        print(f"🔄 ترجمه: {translated if translated else 'ناموفق'}")
    
    print("\n" + "="*60)
