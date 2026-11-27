
import sqlite3

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_NAME = os.path.join(BASE_DIR, "data", "twitter_intelligence.db")


def get_connection():
    return sqlite3.connect(DB_NAME)


def initialize_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            post_id TEXT PRIMARY KEY,
            topic TEXT NOT NULL,
            text TEXT NOT NULL,
            author TEXT,
            date TEXT,
            url TEXT,
            likes INTEGER DEFAULT 0,
            reposts INTEGER DEFAULT 0,
            replies INTEGER DEFAULT 0,
            language TEXT,
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    initialize_analysis_table()
    initialize_claim_tables()


def save_post(post):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO posts
        (post_id, topic, text, author, date, url,
         likes, reposts, replies, language)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        post["post_id"],
        post["topic"],
        post["text"],
        post.get("author"),
        post.get("date"),
        post.get("url"),
        post.get("likes", 0),
        post.get("reposts", 0),
        post.get("replies", 0),
        post.get("language")
    ))

    inserted = cursor.rowcount
    conn.commit()
    conn.close()

    return inserted


def get_posts(topic=None):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if topic:
        cursor.execute(
            "SELECT * FROM posts WHERE topic LIKE ? ORDER BY date DESC",
            (f"%{topic}%",)
        )
    else:
        cursor.execute("SELECT * FROM posts ORDER BY date DESC")

    results = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return results


def initialize_analysis_table():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS post_analyses (
            post_id TEXT PRIMARY KEY,
            text_hash TEXT NOT NULL,
            model TEXT NOT NULL,
            result_json TEXT NOT NULL,
            analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (post_id) REFERENCES posts(post_id)
        )
    """)

    conn.commit()
    conn.close()


def get_cached_analysis(post_id, text_hash):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT result_json FROM post_analyses
        WHERE post_id = ? AND text_hash = ?
    """, (post_id, text_hash))

    row = cursor.fetchone()
    conn.close()

    return row[0] if row else None


def save_analysis(post_id, text_hash, model, result_json):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO post_analyses
        (post_id, text_hash, model, result_json)
        VALUES (?, ?, ?, ?)
    """, (post_id, text_hash, model, result_json))

    conn.commit()
    conn.close()


def initialize_claim_tables():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS claim_groups (
            group_id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            claim_title TEXT,
            claim_summary TEXT,
            earliest_post_date TEXT,
            total_posts INTEGER DEFAULT 0,
            total_authors INTEGER DEFAULT 0,
            total_languages INTEGER DEFAULT 0,
            total_engagement INTEGER DEFAULT 0,
            risk_level TEXT,
            human_verification_required INTEGER DEFAULT 1
        )
    """)

    columns = [
        row[1] for row in cursor.execute(
            "PRAGMA table_info(claim_groups)"
        ).fetchall()
    ]

    if "risk_explanation" not in columns:
        cursor.execute(
            "ALTER TABLE claim_groups ADD COLUMN risk_explanation TEXT"
        )

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS post_claim_groups (
            post_id TEXT PRIMARY KEY,
            group_id INTEGER NOT NULL,
            similarity_score REAL,
            FOREIGN KEY (post_id) REFERENCES posts(post_id),
            FOREIGN KEY (group_id) REFERENCES claim_groups(group_id)
        )
    """)

    conn.commit()
    conn.close()



def get_claim_groups():
    conn = get_connection()
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM claim_groups
        ORDER BY total_posts DESC
    """)

    results = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return results


def get_group_posts(group_id):
    conn = get_connection()
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.*, pcg.similarity_score, a.result_json
        FROM posts p
        JOIN post_claim_groups pcg
            ON p.post_id = pcg.post_id
        JOIN post_analyses a
            ON p.post_id = a.post_id
        WHERE pcg.group_id = ?
        ORDER BY p.date ASC
    """, (group_id,))

    results = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return results


if __name__ == "__main__":
    initialize_database()
    print("Database initialized successfully!")
