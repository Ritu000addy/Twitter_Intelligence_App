from itertools import combinations
from backend.intelligence.claim_grouping import (
    load_analyzed_posts,
    MODEL_NAME,
    THRESHOLD
)
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

posts = load_analyzed_posts()

model = SentenceTransformer(MODEL_NAME)

embeddings = model.encode(
    [p["main_claim"] for p in posts],
    convert_to_numpy=True,
    normalize_embeddings=True
)

similarities = cosine_similarity(embeddings)

from backend.database import get_connection

conn = get_connection()
rows = conn.execute(
    "SELECT post_id, group_id FROM post_claim_groups"
).fetchall()
conn.close()

group_map = {post_id: group_id for post_id, group_id in rows}

print(f"\nThreshold: {THRESHOLD}")
print("\nTop cross-language matches:\n")

matches = []

for i, j in combinations(range(len(posts)), 2):
    if posts[i]["topic"] != posts[j]["topic"]:
        continue

    if posts[i]["language"] == posts[j]["language"]:
        continue

    score = float(similarities[i][j])

    if score >= 0.70:
        matches.append((score, posts[i], posts[j]))

matches.sort(key=lambda x: x[0], reverse=True)

for score, first, second in matches[:30]:
    print("=" * 70)
    print(f"Similarity: {score:.3f} | Topic: {first['topic']}")
    print(f"Languages: {first['language']} / {second['language']}")
    print(f"Stances: {first['stance']} / {second['stance']}")
    print(f"Authors: {first['author']} / {second['author']}")
    print(f"Post IDs: {first['post_id']} / {second['post_id']}")
    print(f"Claim 1: {first['main_claim']}")
    print(f"Claim 2: {second['main_claim']}")

print("\nLOW-SIMILARITY PAIRS (potential unrelated claims):")

low_matches = []

for i, j in combinations(range(len(posts)), 2):
    if posts[i]["topic"] != posts[j]["topic"]:
        continue

    score = float(similarities[i][j])
    if score < THRESHOLD:
        low_matches.append((score, posts[i], posts[j]))

low_matches.sort(key=lambda x: x[0])

for score, first, second in low_matches[:15]:
    print("=" * 70)
    print(f"Similarity: {score:.3f} | Topic: {first['topic']}")
    print(f"Claim 1: {first['main_claim']}")
    print(f"Claim 2: {second['main_claim']}")
    print(f"Post IDs: {first['post_id']} / {second['post_id']}")
    print(f"Group IDs: {group_map.get(first['post_id'])} / {group_map.get(second['post_id'])}")

print("\nGrouping quality review completed.")
