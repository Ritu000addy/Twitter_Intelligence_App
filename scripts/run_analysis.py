from backend.database import initialize_database, get_posts
from backend.intelligence.claim_extractor import analyze_post
import time

initialize_database()

posts = get_posts()

print(f"Total posts: {len(posts)}")

for i, post in enumerate(posts, 1):
    try:
        time.sleep(1)
        result = analyze_post(
            post["text"],
            post["topic"],
            post_id=post["post_id"]
        )

        status = "ERROR" if "error" in result else "DONE"
        print(f"{i}/{len(posts)} | {post['topic']} | {status}")

    except Exception as e:
        print(f"{i}/5 | ERROR: {e}")

print("Batch test completed.")