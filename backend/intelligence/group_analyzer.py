import json
from collections import Counter
from backend.database import get_group_posts
from collections import defaultdict


def analyze_group(group_id):
    posts = get_group_posts(group_id)

    if not posts:
        return None

    authors = set()
    languages = set()
    stances = Counter()
    risks = []
    dates = []

    total_engagement = 0

    for post in posts:
        if post["author"]:
            authors.add(post["author"])

        if post["date"]:
            dates.append(post["date"])


        total_engagement += (
            (post["likes"] or 0)
            + (post["reposts"] or 0)
            + (post["replies"] or 0)
        )

        try:
            result = json.loads(post["result_json"])
        except (json.JSONDecodeError, TypeError):
            continue

        if result.get("language"):
            languages.add(result["language"])

        stances[result.get("stance", "unclear")] += 1

        if result.get("risk_level"):
            risks.append(result["risk_level"])

    risk_order = ["none", "low", "medium", "high"]

    highest_risk = max(
        risks,
        key=lambda r: risk_order.index(r)
        if r in risk_order else 0,
        default="none"
    )    

    spread_over_time = defaultdict(int)

    for date in dates:
        day = date[:10]
        spread_over_time[day] += 1

    return {
        "group_id": group_id,
        "total_posts": len(posts),
        "total_authors": len(authors),
        "total_languages": len(languages),
        "languages": sorted(languages),
        "earliest_post_date": min(dates) if dates else None,
        "latest_post_date": max(dates) if dates else None,
        "total_engagement": total_engagement,
        "supporting_posts": stances["supports"],
        "denying_posts": stances["denies"],
        "neutral_posts": stances["neutral"],
        "unclear_posts": stances["unclear"],
        "highest_risk": highest_risk,
        "human_verification_required": (
            highest_risk in {"medium", "high"}
            or stances["unclear"] > 0
        ),
        "spread_over_time": dict(sorted(spread_over_time.items())),
    }