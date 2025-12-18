from googletrans import Translator

translator = Translator()

def translate_title(title: str) -> str:
    try:
        return translator.translate(title, src="en", dest="fa").text
    except Exception:
        return title  # fallback
