import sqlite3
from backend.database import DB_NAME

conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM post_analyses")
analysed = cursor.fetchone()[0]

cursor.execute("""
    SELECT COUNT(*) FROM post_analyses
    WHERE json_valid(result_json)
""")
valid = cursor.fetchone()[0]

cursor.execute("""
    SELECT COUNT(*) FROM post_analyses
    WHERE json_extract(result_json, '$.is_claim') = 1
""")
claims = cursor.fetchone()[0]

cursor.execute("""
    SELECT COUNT(*) FROM post_analyses
    WHERE json_extract(result_json, '$.is_claim') = 0
""")
non_claims = cursor.fetchone()[0]

conn.close()

print("Analysed posts:", analysed)
print("Valid JSON results:", valid)
print("Extracted claims:", claims)
print("Non-claim posts:", non_claims)