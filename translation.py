"""
ماژول ترجمه اخبار
- Google Translate (deep-translator)
- Persian Cleanup سبک (بدون hazm)
- Rewrite قاعده‌محور برای نقد و بررسی
- مناسب Railway (Image سبک)
"""

import time
import logging
import re
from typing import Optional, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ======================================
# Google Translate
# ======================================
google_translator = None

try:
    from deep_translator import GoogleTranslator
    google_translator = GoogleTranslator(source="en", target="fa")

    test = google_translator.translate("Hello world")
    logger.info(f"✅ Google Translate فعال: {test}")

except ImportError:
    logger.error("❌ deep-translator نصب نیست!")
    google_translator = None
except Exception as e:
    logger.error(f"❌ Google Translate خطا دارد: {e}")
    google_translator = None


# ======================================
# Persian Cleanup (Mini Normalizer)
# ======================================
PERSIAN_CHAR_FIXES = {
    "ي": "ی",
    "ك": "ک",
}

HALF_SPACE_RULES = [
    (r"\bمی\s+", "می‌"),
    (r"\bنمی\s+", "نمی‌"),
    (r"\bخواهد\s+", "خواهد "),
]

def fa_cleanup(text: str) -> str:
    if not text:
        return text

    # حروف عربی → فارسی
    for k, v in PERSIAN_CHAR_FIXES.items():
        text = text.replace(k, v)

    # نیم‌فاصله افعال
    for pattern, repl in HALF_SPACE_RULES:
        text = re.sub(pattern, repl, text)

    # فاصله‌های اضافی
    text = re.sub(r"\s{2,}", " ", text)

    return text.strip()


# ======================================
# Rewrite خبری (برای نقد و بررسی)
# ======================================
REWRITE_RULES = [
    ("دیوار چهارم", "مرز میان فیلم و مخاطب"),
    ("در بهترین زمان‌ها", ""),
    ("آزمایشی است", "به چالش کشیده می‌شود"),
    ("قاچاق کرده است", "وارد کرده است"),
    ("قاچاق کرده", "وارد کرده"),
    ("بینندگان خود را", "تماشاگر را"),
    ("که در پوششی", "و در این مسیر"),
]

def news_rewrite_fa(text: str) -> str:
    if not text:
        return text

    for old, new in REWRITE_RULES:
        text = text.replace(old, new)

    return text.strip()


# ======================================
# Translation Core
# ======================================
def translate_with_google(text: str) -> Optional[str]:
    if not google_translator:
        return None

    try:
        if len(text) > 5000:
            text = text[:5000]

        return google_translator.translate(text)

    except Exception as e:
        logger.error(f"❌ خطای Google Translate: {str(e)[:100]}")
        return None


def translate_to_persian(text: str) -> Optional[str]:
    if not text or len(text.strip()) < 3:
        return None

    text = text.strip()
    logger.debug(f"🌐 ترجمه: {text[:80]}...")

    result = translate_with_google(text)
    if not result:
        return None

    # مرحله ۱: تمیزکاری فارسی
    result = fa_cleanup(result)

    # مرحله ۲: rewrite فقط برای متن‌های تحلیلی
    if any(k in result for k in ["مستند", "نقد", "بررسی", "فیلم", "کارگردان"]):
        result = news_rewrite_fa(result)

    return result


def translate_with_fallback(text: str) -> str:
    translated = translate_to_persian(text)
    if translated:
        return translated

    logger.warning(f"⚠️ بازگشت به متن اصلی: {text[:50]}...")
    return text


def translate_title(text: str) -> str:
    return translate_with_fallback(text)


def batch_translate(texts: List[str], delay: float = 0.5) -> List[str]:
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
    print("🧪 تست سیستم ترجمه خبری (نسخه سبک)")
    print("=" * 60)

    test_texts = [
        "Breaking: Christopher Nolan wins Best Director Oscar",
        "All Walls Collapse: A Year After the LA Fires shows hope rising from the ashes",
        "Timoner’s films often break the fourth wall in experimental ways",
    ]

    for text in test_texts:
        print(f"\n📝 اصلی: {text}")
        print(f"🔄 ترجمه: {translate_to_persian(text)}")

    print("\n" + "=" * 60)
