# category.py

CATEGORIES = {
    "🎬 فیلم": [
        "film", "movie", "cinema", "director", "screenplay", "plot"
    ],
    "📺 سریال": [
        "tv", "series", "episode", "season", "streaming", "netflix", "hbo"
    ],
    "🎭 جشنواره و جوایز": [
        "oscar", "cannes", "festival", "award", "golden globe", "nomination", "winner"
    ],
    "👤 بازیگران و عوامل": [
        "actor", "actress", "director", "producer", "cast", "star", "celebrity"
    ]
}

def classify_category(title, summary):
    """
    دسته‌بندی خبر بر اساس کلمات کلیدی
    """
    text = f"{title} {summary}".lower()

    for category, keywords in CATEGORIES.items():
        for keyword in keywords:
            if keyword in text:
                return category
    
    # اگر هیچ کلمه‌ای پیدا نشد، پیش‌فرض فیلم
    return "🎬 فیلم"
