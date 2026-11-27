
from backend.intelligence.claim_extractor import analyze_post
from backend.database import initialize_database

initialize_database()

tests = [
    {
        "topic": "E20 Petrol",
        "text": "E20 पेट्रोल से गाड़ियों के इंजन खराब हो रहे हैं।"
    },
    {
        "topic": "E20 Petrol",
        "text": "E20 petrol does not damage engines. Claims of engine damage are misleading."
    },
    {
        "topic": "E20 Petrol",
        "text": "I filled E20 petrol in my car today."
    }
]

for i, test in enumerate(tests, 1):
    print(f"\n--- TEST {i} ---")
    print(analyze_post(test["text"],
    test["topic"],
    post_id=f"CACHE_TEST_{i:03d}"
))
