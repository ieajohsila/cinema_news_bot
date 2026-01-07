"""
ماژول ترجمه با Google Translate
Gemini موقتاً غیرفعال شده
+ Persian News Cleanup (Hazm)
"""

import os
import time
import logging
from typing import Optional, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ======================================
# Gemini موقتاً غیرفعال
# ======================================
GEMINI_ENABLED = False
gemini_client = None

logger.info("=" * 60)
logger.info("🔧 سیستم ترجمه - Gemini غیرفعال")
logger.info("=" * 60)

# ======================================
# Google Translate (فعال)
# ======================================
google_translator = None

try:
    from deep_translator import GoogleTranslator
    google_translator = GoogleTranslator(source="en", target="fa")

    test = google_translator.translate("Hello")
    logger.info(f"✅ Google Translate فعال: Hello → {test}")

except ImportError:
    logger.error("❌ deep-translator نصب نیست!")
    logger.error("   نصب: pip install deep-translator")
    google_translator = None
except Exception as e:
    logger.error(f"❌ Google Translate غیرفعال: {e}")
    google_translator = None

if google_translator:
    logger.info("🎯 استراتژی: Google Translate + Persian Cleanup")
else:
    logger.error("❌ هیچ سرویس ترجمه‌ای فعال نیست!")

logger.info("=" * 60 + "\n")

# ======================================
# Persian Cleanup (Hazm)
# ======================================
normalizer = None

try:
    from hazm import Normalizer

    normalizer = Normalizer()
    logger.info("✅ Hazm Normalizer فعال (اصلاح فارسی)")
except Exception as e:
    logger.error(f"⚠️ Hazm در دسترس نیست: {e}")
    normalizer = None


NEWS_STYLE_FIXES = {
    "خواهد شد": "می‌شود",
    "گفته است": "گفت",
    "اعلام کرده است": "اعلام کرد",
    "بیان کرده است": "گفت",
    "منتشر شده است": "منتشر شد",
    "افزایش یافته است": "افزایش یافت",
}


def fa_cleanup(text: str) -> str:
    """اصلاح فارسی استاندارد + لحن خبری"""
    if not text:
        return text

    if normalizer:
        text = normalizer.normalize(text)

    for k, v in NEWS_STYLE_FIXES.items():
        text = text.replace(k, v)

    return text


# ======================================
# Translation Functions (بدون تغییر امضا)
# ======================================
def translate_with_google(text: str) -> Optional[str]:
    """ترجمه با Google Translate"""
    if not google_translator:
        return None

    try:
        if len(text) > 5000:
            text = text[:5000]

        result = google_translator.translate(text)
        return result

    except Exception as e:
        logger.error(f"❌ خطای Google Translate: {str(e)[:100]}")

    return None


def translate_to_persian(text: str) -> Optional[str]:
    """ترجمه اصلی - Google + Persian Cleanup"""

    if not text or len(text.strip()) < 3:
        return None

    text = text.strip()
    logger.debug(f"🌐 ترجمه: {text[:80]}...")

    if google_translator:
        result = translate_with_google(text)
        if result:
            result = fa_cleanup(result)
            logger.debug(f"✅ ترجمه نهایی: {result[:80]}...")
            return result

    logger.error(f"❌ ترجمه ناموفق: {text[:50]}...")
    return None


def translate_with_fallback(text: str) -> str:
    """ترجمه با fallback به متن اصلی"""
    translated = translate_to_persian(text)

    if translated:
        return translated

    logger.warning(f"⚠️ بازگشت به متن اصلی: {text[:50]}...")
    return text


def translate_title(text: str) -> str:
    """تابع قدیمی - سازگاری"""
    return translate_with_fallback(text)


def batch_translate(texts: List[str], delay: float = 0.5) -> List[str]:
    """ترجمه دسته‌ای"""
    results = []

    for text in texts:
        results.append(translate_with_fallback(text))

        if delay > 0:
            time.sleep(delay)

    return results


# ======================================
# Test
# ======================================
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🧪 تست سیستم ترجمه خبری")
    print("=" * 60)

    test_texts = [
        "Breaking: Christopher Nolan wins Best Director Oscar",
        "Marvel releases stunning new trailer",
        "Netflix announces record subscriber growth",
    ]

    for text in test_texts:
        print(f"\n📝 اصلی: {text}")
        result = translate_to_persian(text)
        print(f"🔄 ترجمه: {result if result else 'ناموفق'}")

    print("\n" + "=" * 60)
"""
ماژول ترجمه با Google Translate
Gemini موقتاً غیرفعال شده
+ Persian News Cleanup (Hazm)
"""

import os
import time
import logging
from typing import Optional, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ======================================
# Gemini موقتاً غیرفعال
# ======================================
GEMINI_ENABLED = False
gemini_client = None

logger.info("=" * 60)
logger.info("🔧 سیستم ترجمه - Gemini غیرفعال")
logger.info("=" * 60)

# ======================================
# Google Translate (فعال)
# ======================================
google_translator = None

try:
    from deep_translator import GoogleTranslator
    google_translator = GoogleTranslator(source="en", target="fa")

    test = google_translator.translate("Hello")
    logger.info(f"✅ Google Translate فعال: Hello → {test}")

except ImportError:
    logger.error("❌ deep-translator نصب نیست!")
    logger.error("   نصب: pip install deep-translator")
    google_translator = None
except Exception as e:
    logger.error(f"❌ Google Translate غیرفعال: {e}")
    google_translator = None

if google_translator:
    logger.info("🎯 استراتژی: Google Translate + Persian Cleanup")
else:
    logger.error("❌ هیچ سرویس ترجمه‌ای فعال نیست!")

logger.info("=" * 60 + "\n")

# ======================================
# Persian Cleanup (Hazm)
# ======================================
normalizer = None

try:
    from hazm import Normalizer

    normalizer = Normalizer()
    logger.info("✅ Hazm Normalizer فعال (اصلاح فارسی)")
except Exception as e:
    logger.error(f"⚠️ Hazm در دسترس نیست: {e}")
    normalizer = None


NEWS_STYLE_FIXES = {
    "خواهد شد": "می‌شود",
    "گفته است": "گفت",
    "اعلام کرده است": "اعلام کرد",
    "بیان کرده است": "گفت",
    "منتشر شده است": "منتشر شد",
    "افزایش یافته است": "افزایش یافت",
}


def fa_cleanup(text: str) -> str:
    """اصلاح فارسی استاندارد + لحن خبری"""
    if not text:
        return text

    if normalizer:
        text = normalizer.normalize(text)

    for k, v in NEWS_STYLE_FIXES.items():
        text = text.replace(k, v)

    return text


# ======================================
# Translation Functions (بدون تغییر امضا)
# ======================================
def translate_with_google(text: str) -> Optional[str]:
    """ترجمه با Google Translate"""
    if not google_translator:
        return None

    try:
        if len(text) > 5000:
            text = text[:5000]

        result = google_translator.translate(text)
        return result

    except Exception as e:
        logger.error(f"❌ خطای Google Translate: {str(e)[:100]}")

    return None


def translate_to_persian(text: str) -> Optional[str]:
    """ترجمه اصلی - Google + Persian Cleanup"""

    if not text or len(text.strip()) < 3:
        return None

    text = text.strip()
    logger.debug(f"🌐 ترجمه: {text[:80]}...")

    if google_translator:
        result = translate_with_google(text)
        if result:
            result = fa_cleanup(result)
            logger.debug(f"✅ ترجمه نهایی: {result[:80]}...")
            return result

    logger.error(f"❌ ترجمه ناموفق: {text[:50]}...")
    return None


def translate_with_fallback(text: str) -> str:
    """ترجمه با fallback به متن اصلی"""
    translated = translate_to_persian(text)

    if translated:
        return translated

    logger.warning(f"⚠️ بازگشت به متن اصلی: {text[:50]}...")
    return text


def translate_title(text: str) -> str:
    """تابع قدیمی - سازگاری"""
    return translate_with_fallback(text)


def batch_translate(texts: List[str], delay: float = 0.5) -> List[str]:
    """ترجمه دسته‌ای"""
    results = []

    for text in texts:
        results.append(translate_with_fallback(text))

        if delay > 0:
            time.sleep(delay)

    return results


# ======================================
# Test
# ======================================
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🧪 تست سیستم ترجمه خبری")
    print("=" * 60)

    test_texts = [
        "Breaking: Christopher Nolan wins Best Director Oscar",
        "Marvel releases stunning new trailer",
        "Netflix announces record subscriber growth",
    ]

    for text in test_texts:
        print(f"\n📝 اصلی: {text}")
        result = translate_to_persian(text)
        print(f"🔄 ترجمه: {result if result else 'ناموفق'}")

    print("\n" + "=" * 60)
