"""
ماژول ترجمه و پردازش متن با Google Gemini
- ترجمه انگلیسی به فارسی
- fallback امن
- لاگ شفاف
- سازگار با scheduler و bot async
"""

import os
import time
import logging
from typing import Optional, List
import google.generativeai as genai

# -------------------------------------------------
# Logger
# -------------------------------------------------
logger = logging.getLogger(__name__)

# -------------------------------------------------
# Gemini Config
# -------------------------------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

model = None

if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)

        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=(
                "You are a professional English-to-Persian translator. "
                "Translate any English input into fluent, natural Persian. "
                "Preserve the original tone (formal or informal). "
                "Return ONLY the translated Persian text, nothing else."
            )
        )

        logger.info("✅ Gemini model initialized successfully")

    except Exception as e:
        logger.error(f"❌ Failed to initialize Gemini model: {e}", exc_info=True)
        model = None
else:
    logger.warning("⚠️ GEMINI_API_KEY not found. Translation is disabled.")


# -------------------------------------------------
# Core Translation
# -------------------------------------------------
def translate_to_persian(text: str, max_retries: int = 2) -> Optional[str]:
    """
    ترجمه متن انگلیسی به فارسی با Gemini

    Args:
        text: متن انگلیسی
        max_retries: تعداد تلاش مجدد

    Returns:
        متن فارسی یا None
    """

    if not model:
        logger.error("❌ Gemini model is not available")
        return None

    if not text or not text.strip():
        return None

    text = text.strip()

    if len(text) < 3:
        return None

    logger.info(f"🌐 Translating text: {text[:80]}...")

    for attempt in range(1, max_retries + 2):
        try:
            response = model.generate_content(text)

            if not response or not response.text:
                logger.warning(
                    f"⚠️ Empty response from Gemini (attempt {attempt})"
                )
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

            logger.info(
                f"✅ Translation success: {translated[:80]}..."
            )
            return translated

        except Exception as e:
            logger.error(
                f"❌ Translation error (attempt {attempt}): {e}",
                exc_info=True
            )

            if attempt >= max_retries + 1:
                logger.error(
                    f"❌ Translation failed after {attempt} attempts"
                )
                return None

            time.sleep(1)

    return None


# -------------------------------------------------
# Fallback Wrapper (برای استفاده امن در bot)
# -------------------------------------------------
def translate_with_fallback(text: str) -> str:
    """
    ترجمه با fallback:
    اگر ترجمه fail شود، متن اصلی برمی‌گردد
    """

    translated = translate_to_persian(text)

    if not translated:
        logger.warning("⚠️ Translation failed, returning original text")
        return text

    return translated


# -------------------------------------------------
# Backward Compatibility
# -------------------------------------------------
def translate_title(text: str) -> str:
    """
    alias قدیمی برای سازگاری با نسخه‌های قبلی
    """
    return translate_with_fallback(text)


# -------------------------------------------------
# Batch Translation
# -------------------------------------------------
def batch_translate(texts: List[str], delay: float = 0.5) -> List[str]:
    """
    ترجمه لیستی از متون

    Args:
        texts: لیست متن‌ها
        delay: تأخیر بین درخواست‌ها (ثانیه)

    Returns:
        لیست متون ترجمه‌شده
    """

    results = []

    for text in texts:
        translated = translate_with_fallback(text)
        results.append(translated)

        if delay > 0:
            time.sleep(delay)

    return results


# -------------------------------------------------
# Manual Test
# -------------------------------------------------
if __name__ == "__main__":
    test_text = "Breaking: New Spielberg Movie Announced for 2025"
    print("Original:", test_text)
    print("Translated:", translate_to_persian(test_text))
