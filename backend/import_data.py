
import pandas as pd
from backend.database import initialize_database, save_post

def import_csv(file_path):
    initialize_database()

    df = pd.read_csv(file_path)

    required = ["post_id", "topic", "text", "author",
                "date", "url", "likes", "reposts", "replies"]

    missing = [col for col in required if col not in df.columns]

    if missing:
        print("Missing columns:", missing)
        return

    inserted = 0
    duplicates = 0

    for _, row in df.iterrows():
        post = row.to_dict()

        if pd.isna(post["post_id"]) or pd.isna(post["text"]):
            continue

        post["post_id"] = str(post["post_id"])

        for field in ["author", "date", "url", "language"]:
            if pd.isna(post.get(field)):
                post[field] = None

        for field in ["likes", "reposts", "replies"]:
            if pd.isna(post.get(field)):
                post[field] = 0

        if save_post(post):
            inserted += 1
        else:
            duplicates += 1

    print(f"New posts imported: {inserted}")
    print(f"Duplicates skipped: {duplicates}")


if __name__ == "__main__":
    path = input("Enter CSV file path: ").strip()
    import_csv(path)
