"""
ماژول ترجمه هوشمند با سه سطح:
1. Gemini (با امتحان مدل‌های مختلف)
2. Google Translate رایگان (fallback)
3. متن اصلی (اگر همه ناموفق بودند)
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
# تلاش برای Gemini با مدل‌های مختلف
# -------------------------------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
gemini_model = None
active_model_name = None

if GEMINI_API_KEY:
    try:
        import google.generativeai as genai
        
        logger.info("⏳ پیکربندی Gemini...")
        genai.configure(api_key=GEMINI_API_KEY)
        
        # لیست مدل‌های Gemini به ترتیب اولویت
        model_names = [
            "gemini-1.5-flash-latest",
            "gemini-1.5-flash-002",
            "gemini-1.5-flash",
            "gemini-1.5-pro-latest",
            "gemini-pro",
            "gemini-1.0-pro-latest",
            "gemini-1.0-pro"
        ]
        
        # امتحان هر مدل
        for model_name in model_names:
            try:
                logger.info(f"   🔍 امتحان مدل: {model_name}")
                temp_model = genai.GenerativeModel(model_name)
                
                # تست سریع
                test = temp_model.generate_content("Translate to Persian: Hello", 
                                                   request_options={"timeout": 5})
                
                if test and test.text and len(test.text.strip()) > 0:
                    gemini_model = temp_model
                    active_model_name = model_name
                    logger.info(f"✅ Gemini فعال شد با مدل: {model_name}")
                    logger.info(f"   تست: Hello → {test.text.strip()[:50]}")
                    break
                    
            except Exception as model_error:
                logger.debug(f"   ❌ {model_name} کار نکرد: {str(model_error)[:100]}")
                continue
        
        if not gemini_model:
            logger.warning("⚠️ هیچ مدل Gemini قابل استفاده نبود")
            
    except Exception as e:
        logger.error(f"❌ خطا در راه‌اندازی Gemini: {e}")
        gemini_model = None
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
    if test:
        logger.info("✅ Google Translate (fallback) فعال است")
        logger.info(f"   تست: Hello → {test[:50]}")
    else:
        google_translator = None
        
except ImportError:
    logger.warning("⚠️ deep-translator نصب نیست (pip install deep-translator)")
    google_translator = None
except Exception as e:
    logger.warning(f"⚠️ Google Translate غیرفعال: {e}")
    google_translator = None

# -------------------------------------------------
# گزارش نهایی
# -------------------------------------------------
if gemini_model and google_translator:
    logger.info("🎯 استراتژی: Gemini (اولویت) + Google Translate (پشتیبان)")
elif gemini_model:
    logger.info("🎯 استراتژی: فقط Gemini")
elif google_translator:
    logger.info("🎯 استراتژی: فقط Google Translate")
else:
    logger.error("❌ هیچ سرویس ترجمه فعال نیست - متن‌ها ترجمه نمی‌شوند!")


# -------------------------------------------------
# ترجمه با Gemini
# -------------------------------------------------
def translate_with_gemini(text: str, max_retries: int = 2) -> Optional[str]:
    """ترجمه با Gemini"""
    if not gemini_model:
        return None
    
    for attempt in range(1, max_retries + 1):
        try:
            prompt = f"""Translate this English text to fluent Persian. Return ONLY the Persian translation:

{text}"""
            
            response = gemini_model.generate_content(
                prompt,
                request_options={"timeout": 10}
            )
            
            if response and response.text:
                result = response.text.strip()
                
                # حذف پیشوندهای مزاحم
                prefixes = ["ترجمه:", "Translation:", "Persian:", "ترجمه فارسی:"]
                for prefix in prefixes:
                    if result.startswith(prefix):
                        result = result[len(prefix):].strip()
                
                if len(result) > 0:
                    return result
            
        except Exception as e:
            logger.debug(f"❌ Gemini تلاش {attempt}: {str(e)[:100]}")
            if attempt < max_retries:
                time.sleep(0.5)
    
    return None


# -------------------------------------------------
# ترجمه با Google Translate
# -------------------------------------------------
def translate_with_google(text: str) -> Optional[str]:
    """ترجمه با Google Translate رایگان"""
    if not google_translator:
        return None
    
    try:
        # محدودیت طول
        if len(text) > 4500:
            text = text[:4500]
        
        result = google_translator.translate(text)
        
        if result and len(result.strip()) > 0:
            return result.strip()
        
    except Exception as e:
        logger.debug(f"❌ Google Translate خطا: {str(e)[:100]}")
    
    return None


# -------------------------------------------------
# ترجمه هوشمند (با fallback خودکار)
# -------------------------------------------------
def translate_to_persian(text: str) -> Optional[str]:
    """
    ترجمه هوشمند با اولویت:
    1. Gemini (سریع و با کیفیت)
    2. Google Translate (رایگان و قابل اطمینان)
    3. None (اگر همه ناموفق بودند)
    """
    
    if not text or len(text.strip()) < 3:
        return None
    
    text = text.strip()
    
    logger.info(f"🌐 ترجمه: {text[:60]}...")
    
    # تلاش 1: Gemini
    if gemini_model:
        result = translate_with_gemini(text)
        if result:
            logger.info(f"✅ Gemini ({active_model_name}): {result[:60]}...")
            return result
        logger.debug("⚠️ Gemini ناموفق، تلاش با Google Translate...")
    
    # تلاش 2: Google Translate
    if google_translator:
        result = translate_with_google(text)
        if result:
            logger.info(f"✅ Google Translate: {result[:60]}...")
            return result
        logger.warning("⚠️ Google Translate هم ناموفق بود")
    
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
# تابع قدیمی (سازگاری با کدهای قبلی)
# -------------------------------------------------
def translate_title(text: str) -> str:
    """تابع قدیمی برای سازگاری"""
    return translate_with_fallback(text)


# -------------------------------------------------
# ترجمه دسته‌ای
# -------------------------------------------------
def batch_translate(texts: List[str], delay: float = 0.3) -> List[str]:
    """ترجمه چند متن با تاخیر"""
    results = []
    
    for i, text in enumerate(texts, 1):
        logger.info(f"📝 ترجمه {i}/{len(texts)}")
        results.append(translate_with_fallback(text))
        
        if delay > 0 and i < len(texts):
            time.sleep(delay)
    
    return results


# -------------------------------------------------
# تست دستی
# -------------------------------------------------
if __name__ == "__main__":
    print("\n" + "="*70)
    print("🧪 تست سیستم ترجمه")
    print("="*70)
    
    test_texts = [
        "Breaking: Christopher Nolan wins Best Director Oscar",
        "Marvel releases stunning new trailer for upcoming film",
        "Netflix announces record subscriber growth this quarter"
    ]
    
    print(f"\n🔧 مدل فعال Gemini: {active_model_name if gemini_model else 'غیرفعال'}")
    print(f"🔧 Google Translate: {'فعال' if google_translator else 'غیرفعال'}")
    print("")
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n{i}. 📝 اصلی: {text}")
        result = translate_to_persian(text)
        print(f"   🔄 ترجمه: {result if result else '❌ ناموفق'}")
    
    print("\n" + "="*70)
    print("✅ تست تمام شد")
    print("="*70 + "\n")
