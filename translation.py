from deep_translator import GoogleTranslator

def translate_title(text: str) -> str:
    """ترجمه متن از انگلیسی به فارسی"""
    try:
        if not text or len(text.strip()) == 0:
            return text
        
        # محدود کردن طول متن (GoogleTranslator محدودیت 5000 کاراکتر دارد)
        text = text[:4500]
        
        translator = GoogleTranslator(source='auto', target='fa')
        translated = translator.translate(text)
        
        return translated if translated else text
        
    except Exception as e:
        print(f"⚠️ خطا در ترجمه: {e}")
        return text  # fallback به متن اصلی
