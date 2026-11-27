import json
import pandas as pd

from backend.database import get_connection


def export_claim_data():
    conn = get_connection()

    query = """
        SELECT
            p.post_id,
            p.topic,
            p.text,
            p.author,
            p.date,
            p.url,
            p.likes,
            p.reposts,
            p.replies,
            a.result_json
        FROM posts p
        LEFT JOIN post_analyses a
            ON p.post_id = a.post_id
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    analyses = []

    for value in df["result_json"]:
        try:
            analyses.append(json.loads(value) if value else {})
        except (json.JSONDecodeError, TypeError):
            analyses.append({})

    df["main_claim"] = [a.get("main_claim") for a in analyses]
    df["language"] = [a.get("language") for a in analyses]
    df["stance"] = [a.get("stance") for a in analyses]
    df["sentiment"] = [a.get("sentiment") for a in analyses]
    df["risk_level"] = [a.get("risk_level") for a in analyses]
    df["entities"] = [
        ", ".join(a.get("entities", []))
        for a in analyses
    ]
    df["human_verification_required"] = [
        a.get("human_verification_required")
        for a in analyses
    ]

    output = "data/csv/analyzed_posts.csv"
    df.drop(columns=["result_json"]).to_csv(output, index=False)

    print(f"Exported {len(df)} posts to {output}")


if __name__ == "__main__":
    export_claim_data()