from backend.database import get_posts

for topic in ["E20 Petrol", "UPI Charges", "EVM and Voting"]:
    posts = get_posts(topic)
    print(f"{topic}: {len(posts)}")