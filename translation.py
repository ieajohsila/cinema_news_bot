"""
ماژول ترجمه با استفاده از Google Gemini API
"""
import os
import logging
from typing import Optional
import google.generativeai as genai

# تنظیم logger
logger = logging.getLogger(__name__)

# تنظیم Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')
else:
    logger.warning("GEMINI_API_KEY not found. Translation will be disabled.")
    model = None


def translate_to_persian(text: str, max_retries: int = 2) -> Optional[str]:
    """
    ترجمه متن انگلیسی به فارسی با استفاده از Gemini
    
    Args:
        text: متن انگلیسی برای ترجمه
        max_retries: تعداد تلاش مجدد در صورت خطا
    
    Returns:
        متن ترجمه شده به فارسی یا None در صورت خطا
    """
    if not model:
        logger.error("Gemini model not initialized. Check GEMINI_API_KEY.")
        return None
    
    if not text or not text.strip():
        return None
    
    # حذف فضاهای اضافی
    text = text.strip()
    
    # اگر متن خیلی کوتاه است
    if len(text) < 3:
        return None
    
    # پرامپت برای ترجمه دقیق
    prompt = f"""Translate the following English text to Persian (Farsi). 
Only provide the translation, no explanations or additional text.
Keep the translation natural and fluent.

Text to translate:
{text}

Persian translation:"""
    
    for attempt in range(max_retries + 1):
        try:
            response = model.generate_content(prompt)
            
            if response.text:
                # حذف فضاهای اضافی و خطوط جدید
                translated = response.text.strip()
                
                # حذف عبارات اضافی که گاهی Gemini اضافه می‌کنه
                unwanted_phrases = [
                    "ترجمه:",
                    "Translation:",
                    "Persian translation:",
                    "ترجمه فارسی:",
                ]
                
                for phrase in unwanted_phrases:
                    if translated.startswith(phrase):
                        translated = translated[len(phrase):].strip()
                
                logger.info(f"Successfully translated: {text[:50]}... -> {translated[:50]}...")
                return translated
            else:
                logger.warning(f"Empty response from Gemini on attempt {attempt + 1}")
                
        except Exception as e:
            logger.error(f"Translation error on attempt {attempt + 1}: {e}")
            if attempt == max_retries:
                logger.error(f"Failed to translate after {max_retries + 1} attempts: {text}")
                return None
    
    return None


def translate_with_fallback(text: str) -> str:
    """
    ترجمه با fallback - اگر ترجمه موفق نبود، متن اصلی برمی‌گرده
    
    Args:
        text: متن برای ترجمه
    
    Returns:
        متن ترجمه شده یا متن اصلی
    """
    translated = translate_to_persian(text)
    return translated if translated else text


def batch_translate(texts: list[str], delay: float = 0.5) -> list[str]:
    """
    ترجمه چندین متن به صورت دسته‌ای
    
    Args:
        texts: لیست متون برای ترجمه
        delay: تاخیر بین درخواست‌ها (ثانیه)
    
    Returns:
        لیست متون ترجمه شده
    """
    import time
    
    translated_texts = []
    
    for text in texts:
        translated = translate_with_fallback(text)
        translated_texts.append(translated)
        
        # تاخیر برای جلوگیری از rate limiting
        if delay > 0:
            time.sleep(delay)
    
    return translated_texts


# تست
if __name__ == "__main__":
    # برای تست
    test_text = "Breaking: New Spielberg Movie Announced for 2025"
    result = translate_to_persian(test_text)
    print(f"Original: {test_text}")
    print(f"Translated: {result}")
