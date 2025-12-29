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
logger = logging.getLogger(__name__)

# -------------------------------------------------
# Gemini Config
# -------------------------------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
model = None

if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)

        model = genai.GenerativeModel("gemini-1.5-flash")

        logger.info("✅ Gemini model initialized successfully")

    except Exception as e:
        logger.error(
            f"❌ Failed to initialize Gemini model: {e}",
            exc_info=True
        )
        model = None
else:
    logger.warning("⚠️ GEMINI_API_KEY not found. Translation is disabled.")


# -------------------------------------------------
# Prompt Builder
# -------------------------------------------------
def build_translation_prompt(text: str) -> str:
    return f"""
You are a professional English-to-Persian translator.

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
        logger.error("❌ Gemini model is not available")
        return None

    if not text or not text.strip():
        return None

    text = text.strip()

    if len(text) < 3:
        return None

    prompt = build_translation_prompt(text)

    logger.info(f"🌐 Translating: {text[:80]}...")

    for attempt in range(1, max_retries + 2):
        try:
            response = model.generate_content(prompt)

            if not response or not response.text:
                logger.warning(
                    f"⚠️ Empty response (attempt {attempt})"
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
                logger.error("❌ Translation failed completely")
                return None

            time.sleep(1)

    return None


# -------------------------------------------------
# Fallback Wrapper
# -------------------------------------------------
def translate_with_fallback(text: str) -> str:
    translated = translate_to_persian(text)

    if not translated:
        logger.warning("⚠️ Translation failed, returning original text")
        return text

    return translated


# -------------------------------------------------
# Backward Compatibility
# -------------------------------------------------
def translate_title(text: str) -> str:
    return translate_with_fallback(text)


# -------------------------------------------------
# Batch Translation
# -------------------------------------------------
def batch_translate(texts: List[str], delay: float = 0.5) -> List[str]:
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
    test_text = "Breaking: New Spielberg Movie Announced for 2025"
    print("Original:", test_text)
    print("Translated:", translate_to_persian(test_text))
