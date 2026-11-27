import re
from itertools import combinations

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from backend.database import get_group_posts


THRESHOLD = 0.85


def normalize(text):
    text = (text or "").lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def detect_group_duplicates(group_id):
    posts = get_group_posts(group_id)

    if len(posts) < 2:
        return[]

    texts = [normalize(p["text"]) for p in posts]

    if not any(texts):
        return []

    vectorizer = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(3, 5),
        min_df=1
    )

    vectors = vectorizer.fit_transform(texts)
    similarities = cosine_similarity(vectors)

    flagged_pairs = []

    for i, j in combinations(range(len(posts)), 2):
        score = float(similarities[i, j])

        if score < THRESHOLD:
            continue

        same_author = (
            posts[i]["author"] == posts[j]["author"]
        )

        exact_match = texts[i] == texts[j]

        if exact_match and same_author:
            category = "EXACT DUPLICATE - SAME AUTHOR"
        elif exact_match:
            category = "EXACT DUPLICATE - DIFFERENT AUTHORS"
        elif same_author:
            category = "NEAR DUPLICATE - SAME AUTHOR"
        else:
            category = "NEAR DUPLICATE - DIFFERENT AUTHORS"

        flagged_pairs.append({
            "post_1": posts[i]["post_id"],
            "author_1": posts[i]["author"],
            "post_2": posts[j]["post_id"],
            "author_2": posts[j]["author"],
            "similarity": round(score, 3),
            "category": category,
            "possible_coordination": not same_author
        })

    return flagged_pairs

          
if __name__ == "__main__":
    from backend.database import get_claim_groups

    groups = get_claim_groups()

    total = 0

    for group in groups:
        pairs = detect_group_duplicates(group["group_id"])

        if pairs:
            print(f"\nGroup {group['group_id']}:")
            for pair in pairs:
                print(pair)

        total += len(pairs)

    print(f"\nTotal flagged pairs: {total}")
    print("Flags indicate similarity, not proof of coordination.")
