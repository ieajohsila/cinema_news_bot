"""
سیستم تعیین اهمیت اخبار بر اساس کلمات کلیدی
قابل مدیریت از طریق پنل ادمین
"""

import json
import os

IMPORTANCE_FILE = "data/importance_rules.json"

# قوانین پیش‌فرض
DEFAULT_RULES = {
    "0": {
        "name": "کم‌اهمیت",
        "keywords": ["rumor", "speculation", "might", "شایعه", "احتمال"]
    },
    "1": {
        "name": "معمولی",
        "keywords": ["review", "interview", "نقد", "مصاحبه", "تحلیل", "analysis", "opinion"]
    },
    "2": {
        "name": "مهم",
        "keywords": [
            "trailer", "teaser", "premiere", "release", "box office",
            "تریلر", "اکران", "فروش", "باکس آفیس", 
            "festival", "nomination", "جشنواره", "نامزد"
        ]
    },
    "3": {
        "name": "فوری",
        "keywords": [
            "oscar", "cannes", "award winner", "breaking", "dies", "death",
            "اسکار", "کن", "برنده", "فوری", "فوت", "درگذشت",
            "historic", "record breaking", "تاریخی"
        ]
    }
}


def load_rules():
    """بارگذاری قوانین از فایل"""
    os.makedirs("data", exist_ok=True)
    
    if not os.path.exists(IMPORTANCE_FILE):
        # ساخت فایل پیش‌فرض
        with open(IMPORTANCE_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_RULES, f, ensure_ascii=False, indent=2)
        return DEFAULT_RULES
    
    with open(IMPORTANCE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_rules(rules):
    """ذخیره قوانین در فایل"""
    os.makedirs("data", exist_ok=True)
    with open(IMPORTANCE_FILE, "w", encoding="utf-8") as f:
        json.dump(rules, f, ensure_ascii=False, indent=2)


def get_all_rules():
    """دریافت تمام قوانین"""
    return load_rules()


def get_level_keywords(level):
    """دریافت کلمات یک سطح خاص"""
    rules = load_rules()
    return rules.get(str(level), {}).get("keywords", [])


def add_keyword(level, keyword):
    """افزودن کلمه به یک سطح"""
    rules = load_rules()
    level_str = str(level)
    
    if level_str not in rules:
        rules[level_str] = {"name": f"سطح {level}", "keywords": []}
    
    if keyword not in rules[level_str]["keywords"]:
        rules[level_str]["keywords"].append(keyword)
        save_rules(rules)
        return True
    return False


def remove_keyword(level, keyword):
    """حذف کلمه از یک سطح"""
    rules = load_rules()
    level_str = str(level)
    
    if level_str in rules and keyword in rules[level_str]["keywords"]:
        rules[level_str]["keywords"].remove(keyword)
        save_rules(rules)
        return True
    return False


def add_new_level(level, name, keywords=None):
    """افزودن سطح جدید"""
    rules = load_rules()
    level_str = str(level)
    
    rules[level_str] = {
        "name": name,
        "keywords": keywords or []
    }
    save_rules(rules)


def classify_importance(title, summary):
    """تعیین اهمیت خبر بر اساس کلمات کلیدی"""
    text = f"{title} {summary}".lower()
    rules = load_rules()
    
    # بررسی از بالاترین سطح به پایین‌ترین
    for level in sorted(rules.keys(), key=lambda x: int(x), reverse=True):
        keywords = rules[level].get("keywords", [])
        for keyword in keywords:
            if keyword.lower() in text:
                return int(level)
    
    # پیش‌فرض
    return 1


if __name__ == "__main__":
    # تست
    print("🧪 تست سیستم اهمیت...\n")
    
    # نمایش قوانین فعلی
    rules = get_all_rules()
    for level, data in sorted(rules.items(), key=lambda x: int(x[0])):
        print(f"سطح {level} ({data['name']}): {len(data['keywords'])} کلمه")
    
    # تست تشخیص
    test_title = "Breaking: Director wins Oscar for Best Picture"
    importance = classify_importance(test_title, "")
    print(f"\n📰 \"{test_title}\"")
    print(f"⭐ اهمیت: {importance}")
