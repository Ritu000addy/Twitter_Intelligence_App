
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from backend.database import get_posts

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
SIMILARITY_THRESHOLD = 0.78

def group_posts():
    posts = get_posts()

    if not posts:
        print("No posts found.")
        return

    print(f"Loading {MODEL_NAME}...")
    model = SentenceTransformer(MODEL_NAME)

    texts = [post["text"] for post in posts]

    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar=True
    )

    similarities = cosine_similarity(embeddings)

    groups = []
    assigned = set()

    for i in range(len(posts)):
        if i in assigned:
            continue

        group = [i]
        assigned.add(i)

        for j in range(i + 1, len(posts)):
            if j in assigned:
                continue

            if similarities[i][j] >= SIMILARITY_THRESHOLD:
                group.append(j)
                assigned.add(j)

        if len(group) >= 2:
            groups.append(group)

    print(f"\nPosts analysed: {len(posts)}")
    print(f"Potential claim groups: {len(groups)}")

    for number, group in enumerate(groups, 1):
        print(f"\n--- Potential Claim Group {number} ---")

        for index in group:
            post = posts[index]
            print(f"Language: {post.get('language')}")
            print(f"Author: {post.get('author')}")
            print(f"Text: {post['text'][:300]}")
            print()

if __name__ == "__main__":
    group_posts()
