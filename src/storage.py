import json
import os
from datetime import datetime

HISTORY_FILE = "post_history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_post(post):
    history = load_history()
    # ensure a minimal structure copy so future edits don't mutate saved
    entry = {
        "topic": post.get("topic"),
        "tone": post.get("tone"),
        "headline": post.get("headline"),
        "body": post.get("body"),
        "hashtags": post.get("hashtags", []),
        "user_keywords": post.get("user_keywords", []),
        "adaptive_keywords": post.get("adaptive_keywords", []),
        "cta": post.get("cta", []),
        "predicted_engagement": post.get("predicted_engagement"),
        "extracted_tone": post.get("extracted_tone"),
        "timestamp": datetime.now().isoformat()
    }
    history.append(entry)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

def get_analytics():
    history = load_history()
    if not history:
        return {"total_posts": 0, "average_engagement": 0.0, "tone_distribution": {}}
    # engagement: try to parse numeric prefix from predicted_engagement
    total = 0.0
    count = 0
    tones = {}
    for p in history:
        pe = p.get("predicted_engagement", "")
        import re
        m = re.search(r"([1-9]|10)", str(pe))
        if m:
            total += float(m.group(0))
            count += 1
        t = p.get("tone", "unspecified")
        tones[t] = tones.get(t, 0) + 1
    avg = (total / count) if count else 0.0
    return {"total_posts": len(history), "average_engagement": avg, "tone_distribution": tones}
