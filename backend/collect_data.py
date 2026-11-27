import os
import requests
from dotenv import load_dotenv
from backend.database import initialize_database, save_post, get_posts

load_dotenv()

API_URL = "https://www.socialcrawl.dev/v1/twitter/search/tweets"
API_KEY = os.getenv("SOCIALCRAWL_API_KEY")

TOPICS = {
    "E20 Petrol": [
        '"E20 petrol" (engine OR damage OR mileage OR warranty OR insurance) lang:en',
        '"E20 पेट्रोल" (इंजन OR नुकसान OR माइलेज OR वारंटी) lang:hi',
        '"E20 petrol" (gaadi OR mileage OR engine OR kharab OR nuksan)'
    ],

    "UPI Charges": [
        'UPI (charges OR fees OR tax OR payment limit) lang:en',
        'UPI (चार्ज OR शुल्क OR टैक्स OR लिमिट) lang:hi',
        'UPI (charge OR paisa OR fees OR limit OR lagega)'
    ],

    "EVM and Voting": [
        '(EVM OR voting) (tampering OR mismatch OR manipulation OR denial OR factcheck) lang:en',
        '(EVM OR चुनाव) (छेड़छाड़ OR गड़बड़ी OR वोट OR फैक्ट चेक) lang:hi',
        '(EVM OR voting) (setting OR gadbad OR vote mismatch OR hack)'
    ]
}

def collect_posts(topic, query, max_items=100):
    if not API_KEY:
        print("SOCIALCRAWL_API_KEY missing in .env")
        return

    existing_count = len(get_posts(topic))
    remaining = max(0, max_items - existing_count)

    if remaining == 0:
        print(f"{topic}: already has 100 posts.")
        return

    response = requests.get(
        API_URL,
        headers={"x-api-key": API_KEY},
        params={"query": query, "sort": "latest", "max_items": remaining},
        timeout=30
    )

    response.raise_for_status()
    result = response.json()

    if not result.get("success"):
        print(result)
        return

    items = result.get("data", {}).get("items", [])
    inserted = 0

    for item in items:
        post = item.get("post", {})
        computed = item.get("computed", {})
        author = post.get("author", {})
        content = post.get("content", {})
        engagement = post.get("engagement", {})
        ext = post.get("ext", {})

        post_id = post.get("id")
        text = content.get("text", "").strip()
        

        if not post_id or not text:
            continue

        record = {
            "post_id": post_id,
            "topic": topic,
            "text": text,
            "author": author.get("username"),
            "date": post.get("published_at"),
            "url": post.get("url"),
            "likes": engagement.get("likes", 0),
            "reposts": engagement.get("shares", 0),
            "replies": engagement.get("comments", 0),
            "language": computed.get("language") or ext.get("content_language")
        }

        inserted += save_post(record)

    print(f"Received: {len(items)} | Newly saved: {inserted}")
    print(f"Topic total: {len(get_posts(topic))}/100")
    print("Credits remaining:", result.get("credits_remaining"))

    
if __name__ == "__main__":
    initialize_database()
    for topic, queries in TOPICS.items():
        for query in queries:
            print(f"\nCollecting {topic}: {query}")
            collect_posts(topic, query)

    custom_topic = input("\nEnter a new topic (or press Enter to skip): ").strip()

    if custom_topic:
        custom_query = input("Enter X search query/keywords: ").strip()

        if custom_query:
            collect_posts(custom_topic, custom_query, max_items=100)