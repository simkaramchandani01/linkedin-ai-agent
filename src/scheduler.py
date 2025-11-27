from datetime import datetime, timedelta

def suggest_post_times(n=3):
    """
    Simple heuristic: prefer next workdays at 8:30 AM and 12:00 PM.
    Returns up to n datetimes (local).
    """
    now = datetime.now()
    suggestions = []
    offsets = list(range(1, 8))  # check the next 7 days
    times = [(8, 30), (12, 0), (17, 30)]
    weekdays_allowed = [0, 1, 2, 3, 4]  # Mon-Fri

    for d in offsets:
        day = now + timedelta(days=d)
        if day.weekday() not in weekdays_allowed:
            continue
        for (h, m) in times:
            suggestions.append(day.replace(hour=h, minute=m, second=0, microsecond=0))
            if len(suggestions) >= n:
                return suggestions
    return suggestions[:n]

