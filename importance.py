RULES = {
    3: ["death", "dies", "oscar", "cannes", "wins", "breaking"],
    2: ["trailer", "festival", "box office", "premiere"],
    1: ["review", "interview", "analysis"]
}

def classify_importance(title, summary):
    text = f"{title} {summary}".lower()
    for level in sorted(RULES.keys(), reverse=True):
        for k in RULES[level]:
            if k in text:
                return level
    return 1
