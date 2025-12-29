"""
کلاس Gemini برای ترجمه - مشابه کد نمونه
"""
import os
import logging
import google.generativeai as genai

logger = logging.getLogger(__name__)


class GeminiTranslator:
    """کلاس مدیریت ترجمه با Gemini"""
    
    def __init__(self):
        """مقداردهی اولیه Gemini"""
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-2.0-flash-lite")
        self.model = None
        self.is_available = False
        
        self._initialize()
    
    def _initialize(self):
        """راه‌اندازی مدل Gemini"""
        if not self.api_key:
            logger.warning("⚠️ GEMINI_API_KEY تنظیم نشده")
            return
        
        try:
            logger.info(f"⏳ پیکربندی Gemini با کلید: {self.api_key[:20]}...")
            genai.configure(api_key=self.api_key)
            
            # لیست مدل‌های قابل امتحان
            models_to_try = [
                self.model_name,
                "gemini-2.0-flash-exp",
                "gemini-1.5-flash",
                "gemini-1.5-pro",
                "gemini-pro"
            ]
            
            # امتحان هر مدل
            for model_name in models_to_try:
                try:
                    logger.info(f"   🔍 تست مدل: {model_name}")
                    test_model = genai.GenerativeModel(model_name)
                    
                    # تست سریع
                    response = test_model.generate_content("Say: OK")
                    
                    if response and response.text:
                        self.model = test_model
                        self.model_name = model_name
                        self.is_available = True
                        logger.info(f"✅ مدل {model_name} فعال شد")
                        return
                        
                except Exception as e:
                    logger.debug(f"   ❌ مدل {model_name} کار نکرد: {str(e)[:50]}")
                    continue
            
            logger.error("❌ هیچ مدل Gemini قابل استفاده‌ای یافت نشد")
            
        except Exception as e:
            logger.error(f"❌ خطا در مقداردهی Gemini: {e}")
    
    def translate(self, text: str, source_lang: str = "English", target_lang: str = "Persian") -> str:
        """
        ترجمه متن
        
        Args:
            text: متن مورد نظر برای ترجمه
            source_lang: زبان مبدا
            target_lang: زبان مقصد
        
        Returns:
            متن ترجمه شده یا None در صورت خطا
        """
        if not self.is_available or not self.model:
            logger.error("❌ مدل Gemini در دسترس نیست")
            return None
        
        if not text or len(text.strip()) < 3:
            return None
        
        try:
            prompt = f"""Translate this {source_lang} text to {target_lang}.
Return ONLY the {target_lang} translation with no explanations or labels.

{source_lang} text:
{text}

{target_lang} translation:"""
            
            response = self.model.generate_content(prompt)
            
            if response and response.text:
                result = response.text.strip()
                
                # حذف پیشوندهای مزاحم
                unwanted = ["ترجمه:", "Translation:", "Persian:", "ترجمه فارسی:"]
                for prefix in unwanted:
                    if result.startswith(prefix):
                        result = result[len(prefix):].strip()
                
                logger.info(f"✅ ترجمه Gemini: {text[:50]}... → {result[:50]}...")
                return result
            
            logger.warning("⚠️ پاسخ خالی از Gemini")
            return None
            
        except Exception as e:
            logger.error(f"❌ خطا در ترجمه با Gemini: {e}")
            return None
    
    def get_model_info(self) -> dict:
        """دریافت اطلاعات مدل"""
        return {
            "available": self.is_available,
            "model_name": self.model_name if self.is_available else None,
            "api_key_set": bool(self.api_key)
        }


# -------------------------------------------------
# نمونه Singleton برای استفاده در کل برنامه
# -------------------------------------------------
_gemini_instance = None

def get_gemini_translator() -> GeminiTranslator:
    """دریافت نمونه Singleton از GeminiTranslator"""
    global _gemini_instance
    if _gemini_instance is None:
        _gemini_instance = GeminiTranslator()
    return _gemini_instance


# -------------------------------------------------
# تست
# -------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "="*60)
    print("🧪 تست کلاس GeminiTranslator")
    print("="*60)
    
    translator = GeminiTranslator()
    
    print(f"\n📊 اطلاعات مدل:")
    info = translator.get_model_info()
    for key, value in info.items():
        print(f"   {key}: {value}")
    
    if translator.is_available:
        print("\n🔄 تست ترجمه:")
        test_texts = [
            "Breaking: Christopher Nolan wins Oscar",
            "New Marvel movie announced",
            "Netflix record growth"
        ]
        
        for text in test_texts:
            print(f"\n📝 اصلی: {text}")
            result = translator.translate(text)
            print(f"🔄 ترجمه: {result if result else 'ناموفق'}")
    else:
        print("\n❌ Gemini در دسترس نیست")
    
    print("\n" + "="*60)
