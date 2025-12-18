from deep_translator import GoogleTranslator

def fa(text):
    return GoogleTranslator(source="auto", target="fa").translate(text)
