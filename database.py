import json
import os

DB_FILE = "settings.json"

def load_settings():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_settings(settings):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)

def set_setting(key, value):
    settings = load_settings()
    settings[key] = value
    save_settings(settings)

def get_setting(key):
    settings = load_settings()
    return settings.get(key)
