"""
ماژول ترجمه هوشمند با دو سطح:
1. Gemini (اولویت اول) - API جدید
2. Google Translate رایگان (fallback)
"""

import os
import time
import logging
from typing import Optional, List

# -------------------------------------------------
# Logger
# -------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------------------------------------
# تلاش برای Gemini با API جدید
# -------------------------------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-2.0-flash-exp")
gemini_client = None

logger.info("="*60)
logger.info("🔧 شروع مقداردهی سیستم ترجمه...")
logger.info("="*60)

if GEMINI_API_KEY:
    logger.info(f"✅ GEMINI_API_KEY یافت شد: {GEMINI_API_KEY[:20]}...")
    logger.info(f"🎯 مدل مورد استفاده: {GEMINI_MODEL_NAME}")
    
    try:
        # 🔧 FIX: استفاده از API جدید google-genai
        from google import genai
        
        logger.info("⏳ ایجاد کلاینت Gemini...")
        os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
        
        # تست سریع با مدل‌های مختلف
        models_to_try = [
            GEMINI_MODEL_NAME,
            "gemini-2.0-flash-exp",
            "gemini-1.5-flash",
            "gemini-1.5-pro",
        ]
        
        model_works = False
        for model_name in models_to_try:
            try:
                logger.info(f"   🔍 تست مدل: {model_name}")
                response = gemini_client.models.generate_content(
                    model=model_name,
                    contents="Say OK"
                )
                
                if response and response.text:
                    logger.info(f"✅ مدل {model_name} کار می‌کند!")
                    logger.info(f"   تست: Say OK → {response.text.strip()}")
                    GEMINI_MODEL_NAME = model_name
                    model_works = True
                    break
                    
            except Exception as e:
                logger.debug(f"   ❌ مدل {model_name}: {str(e)[:50]}")
                continue
        
        if not model_works:
            raise Exception("هیچ مدل Gemini کار نکرد")
        
        logger.info("✅ Gemini فعال و آماده است")
            
    except ImportError:
        logger.error("❌ کتابخانه google-genai نصب نیست!")
        logger.error("   نصب کنید: pip install google-genai")
        gemini_client = None
    except Exception as e:
        logger.error(f"❌ خطا در Gemini: {e}")
        logger.warning("⚠️ Gemini غیرفعال شد، fallback به Google Translate")
        gemini_client = None
else:
    logger.warning("⚠️ GEMINI_API_KEY تنظیم نشده")

# -------------------------------------------------
# تلاش برای Deep Translator (fallback)
# -------------------------------------------------
google_translator = None

try:
    from deep_translator import GoogleTranslator
    google_translator = GoogleTranslator(source='en', target='fa')
    
    # تست سریع
    test = google_translator.translate("Hello")
    logger.info(f"✅ Google Translate فعال: Hello → {test}")
    
except ImportError:
    logger.warning("⚠️ deep-translator نصب نیست")
    logger.warning("   نصب: pip install deep-translator")
    google_translator = None
except Exception as e:
    logger.warning(f"⚠️ Google Translate غیرفعال: {e}")
    google_translator = None

# -------------------------------------------------
# انتخاب استراتژی
# -------------------------------------------------
if gemini_client and google_translator:
    logger.info("🎯 استراتژی: Gemini (اولویت اول) + Google Translate (پشتیبان)")
elif gemini_client:
    logger.info("🎯 استراتژی: فقط Gemini")
elif google_translator:
    logger.info("🎯 استراتژی: فقط Google Translate")
else:
    logger.error("❌ هیچ سرویس ترجمه‌ای فعال نیست!")

logger.info("="*60 + "\n")


# -------------------------------------------------
# ترجمه با Gemini (اولویت اول)
# -------------------------------------------------
def translate_with_gemini(text: str) -> Optional[str]:
    """ترجمه با Gemini - API جدید"""
    if not gemini_client:
        return None
    
    try:
        prompt = f"""Translate this English text to Persian. 
Return ONLY the Persian translation with no explanations, labels, or extra text.

English text:
{text}

Persian translation:"""
        
        response = gemini_client.models.generate_content(
            model=GEMINI_MODEL_NAME,
            contents=prompt
        )
        
        if response and response.text:
            result = response.text.strip()
            
            # حذف پیشوندهای مزاحم
            unwanted = ["ترجمه:", "Translation:", "Persian:", "ترجمه فارسی:"]
            for prefix in unwanted:
                if result.startswith(prefix):
                    result = result[len(prefix):].strip()
            
            return result
        
    except Exception as e:
        logger.error(f"❌ خطای Gemini: {type(e).__name__} - {str(e)[:100]}")
    
    return None


# -------------------------------------------------
# ترجمه با Google Translate (fallback)
# -------------------------------------------------
def translate_with_google(text: str) -> Optional[str]:
    """ترجمه با Google Translate - fallback"""
    if not google_translator:
        return None
    
    try:
        # محدودیت طول (5000 کاراکتر)
        if len(text) > 5000:
            text = text[:5000]
        
        result = google_translator.translate(text)
        return result
        
    except Exception as e:
        logger.error(f"❌ خطای Google Translate: {type(e).__name__} - {str(e)[:100]}")
    
    return None


# -------------------------------------------------
# ترجمه هوشمند (با اولویت Gemini)
# -------------------------------------------------
def translate_to_persian(text: str) -> Optional[str]:
    """
    ترجمه هوشمند با اولویت:
    1. اول Gemini امتحان میشه (اولویت اول)
    2. اگه ناموفق بود، Google Translate
    3. اگه اونم ناموفق بود، None
    """
    
    if not text or len(text.strip()) < 3:
        return None
    
    text = text.strip()
    
    logger.debug(f"🌐 ترجمه: {text[:80]}...")
    
    # اولویت 1: Gemini
    if gemini_client:
        logger.debug("   📍 تلاش با Gemini...")
        result = translate_with_gemini(text)
        if result:
            logger.debug(f"✅ Gemini: {result[:80]}...")
            return result
        logger.debug("⚠️ Gemini ناموفق، fallback به Google Translate...")
    
    # اولویت 2: Google Translate
    if google_translator:
        logger.debug("   📍 تلاش با Google Translate...")
        result = translate_with_google(text)
        if result:
            logger.debug(f"✅ Google Translate: {result[:80]}...")
            return result
        logger.debug("⚠️ Google Translate هم ناموفق بود")
    
    logger.error(f"❌ ترجمه کاملاً ناموفق: {text[:50]}...")
    return None


# -------------------------------------------------
# ترجمه با fallback به متن اصلی
# -------------------------------------------------
def translate_with_fallback(text: str) -> str:
    """
    ترجمه می‌کنه، اگه نشد متن اصلی رو برمی‌گردونه
    """
    translated = translate_to_persian(text)
    
    if translated:
        return translated
    
    logger.warning(f"⚠️ بازگشت به متن اصلی: {text[:50]}...")
    return text


# -------------------------------------------------
# تابع قدیمی (سازگاری با کد قبلی)
# -------------------------------------------------
def translate_title(text: str) -> str:
    """تابع قدیمی برای سازگاری با کدهای قبلی"""
    return translate_with_fallback(text)


# -------------------------------------------------
# ترجمه دسته‌ای
# -------------------------------------------------
def batch_translate(texts: List[str], delay: float = 0.5) -> List[str]:
    """ترجمه چند متن با تاخیر"""
    results = []
    
    for text in texts:
        results.append(translate_with_fallback(text))
        
        if delay > 0:
            time.sleep(delay)
    
    return results


# -------------------------------------------------
# تست دستی
# -------------------------------------------------
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 تست سیستم ترجمه")
    print("="*60)
    
    test_texts = [
        "Breaking: Christopher Nolan wins Best Director Oscar",
        "Marvel releases stunning new trailer",
        "Netflix announces record subscriber growth"
    ]
    
    for text in test_texts:
        print(f"\n📝 اصلی: {text}")
        result = translate_to_persian(text)
        print(f"🔄 ترجمه: {result if result else 'ناموفق'}")
    
    print("\n" + "="*60)
