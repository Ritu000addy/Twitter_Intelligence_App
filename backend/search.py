
from backend.database import initialize_database, get_posts

TOPICS = {
    "1": "E20 Petrol",
    "2": "UPI Charges",
    "3": "EVM and Voting"
}


def search_posts(keyword):
    all_posts = get_posts()

    keyword = keyword.lower()

    results = [
        post for post in all_posts
        if keyword in post["text"].lower()
        or keyword in post["topic"].lower()
    ]

    return results


def main():
    initialize_database()

    print("\n===== TWITTER INTELLIGENCE SEARCH =====")

    print("\nSelect a topic:")
    for key, topic in TOPICS.items():
        print(f"{key}. {topic}")

    print("4. Search a new topic")

    choice = input("\nEnter choice: ").strip()

    if choice in TOPICS:
        keyword = TOPICS[choice]
    elif choice == "4":
        keyword = input("Enter your new topic: ").strip()
    else:
        print("Invalid choice")
        return

    results = search_posts(keyword)

    print(f"\nFound {len(results)} matching posts")

    for post in results:
        print("\n------------------------------")
        print("Topic:", post["topic"])
        print("Text:", post["text"])
        print("Author:", post["author"])
        print("Date:", post["date"])
        print("URL:", post["url"])
        print("Likes:", post["likes"])
        print("Reposts:", post["reposts"])
        print("Replies:", post["replies"])


if __name__ == "__main__":
    main()
