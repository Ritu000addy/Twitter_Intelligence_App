import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import sqlite3
import json
import pandas as pd
import streamlit as st
import plotly.express as px

from backend.database import DB_NAME
from backend.intelligence.duplicate_detector import detect_group_duplicates
from backend.intelligence.report_generator import generate_pdf_report


st.set_page_config(
    page_title="Twitter Intelligence",
    page_icon="🔎",
    layout="wide"
)

st.title("Twitter Intelligence Dashboard")
st.caption("Cross-language social media claim monitoring")

conn = sqlite3.connect(DB_NAME)

posts = pd.read_sql_query("""
    SELECT p.*, a.result_json, pcg.group_id
    FROM posts p
    LEFT JOIN post_analyses a ON p.post_id = a.post_id
    LEFT JOIN post_claim_groups pcg ON p.post_id = pcg.post_id
""", conn)

groups = pd.read_sql_query("""
    SELECT * FROM claim_groups
    ORDER BY total_posts DESC
""", conn)

conn.close()

if posts.empty:
    st.warning("No posts available.")
    st.stop()

analyses = []
for value in posts["result_json"]:
    try:
        analyses.append(json.loads(value) if value else {})
    except (json.JSONDecodeError, TypeError):
        analyses.append({})

for field in [
    "main_claim", "language", "stance",
    "sentiment", "risk_level", "evidence_quote",
    "human_verification_required"
]:
    posts[field] = [a.get(field) for a in analyses]

st.sidebar.header("Filters")

topics = ["All"] + sorted(posts["topic"].dropna().unique().tolist())
selected_topic = st.sidebar.selectbox("Topic", topics)

if selected_topic != "All":
    posts = posts[posts["topic"] == selected_topic]
    groups = groups[groups["topic"] == selected_topic]

search = st.sidebar.text_input("Search posts or claims")

if search:
    mask = (
        posts["text"].fillna("").str.contains(search, case=False)
        | posts["main_claim"].fillna("").str.contains(search, case=False)
    )
    posts = posts[mask]

total = len(posts)
analysed = int(posts["result_json"].notna().sum())
claims = int(posts["main_claim"].notna().sum())
high_risk = int((posts["risk_level"] == "high").sum())

c1, c2, c3, c4 = st.columns(4)
c1.metric("Collected Posts", total)
c2.metric("Analysed Posts", analysed)
c3.metric("Extracted Claims", claims)
c4.metric("High-Risk Posts", high_risk)

st.divider()

st.subheader("Intelligence Overview")

left, right = st.columns(2)

with left:
    stance_data = (
        posts["stance"].fillna("Unknown")
        .value_counts()
        .rename_axis("Stance")
        .reset_index(name="Posts")
    )
    if not stance_data.empty:
        fig = px.pie(
            stance_data, names="Stance", values="Posts",
            title="Post Stance Distribution"
        )
        st.plotly_chart(fig, use_container_width=True)

with right:
    risk_data = (
        posts["risk_level"].fillna("Unknown")
        .value_counts()
        .rename_axis("Risk")
        .reset_index(name="Posts")
    )
    if not risk_data.empty:
        fig = px.bar(
            risk_data, x="Risk", y="Posts",
            title="Risk Level Distribution"
        )
        st.plotly_chart(fig, use_container_width=True)

st.divider()

st.subheader("Top Claim Groups")

if groups.empty:
    st.info("No multi-post claim groups available.")
else:
    st.dataframe(
        groups[[
            "group_id", "claim_title", "total_posts",
            "total_authors", "total_languages",
            "total_engagement", "risk_level"
        ]],
        use_container_width=True,
        hide_index=True
    )

st.divider()

st.subheader("Claim Group Details")

if not groups.empty:
    group_options = groups["group_id"].tolist()
    selected_group = st.selectbox("Select claim group", group_options)

    conn = sqlite3.connect(DB_NAME)
    group_posts = pd.read_sql_query("""
        SELECT p.*, pcg.similarity_score, a.result_json
        FROM posts p
        JOIN post_claim_groups pcg ON p.post_id = pcg.post_id
        LEFT JOIN post_analyses a ON p.post_id = a.post_id
        WHERE pcg.group_id = ?
        ORDER BY p.date ASC
    """, conn, params=(selected_group,))
    conn.close()

    selected_data = groups.loc[groups["group_id"] == selected_group].iloc[0]

    st.write(f"**Claim:** {selected_data['claim_title']}")
    st.write(f"**Summary:** {selected_data['claim_summary']}")
    st.write(f"**Risk Level:** {selected_data['risk_level'].upper()}")
    st.info(f"**Why this claim may be risky:** {selected_data['risk_explanation']}")
    st.write(f"**Human verification required:** {'Yes' if selected_data['human_verification_required'] else 'No'}")
    
    group_analyses = []
    for value in group_posts["result_json"]:
        try:
            group_analyses.append(json.loads(value) if value else {})
        except (json.JSONDecodeError, TypeError):
            group_analyses.append({})

    group_posts["stance"] = [a.get("stance") for a in group_analyses]
    group_posts["language"] = [a.get("language") for a in group_analyses]
    group_posts["risk_level"] = [a.get("risk_level") for a in group_analyses]
    group_posts["evidence_quote"] = [a.get("evidence_quote") for a in group_analyses]

    spread = (
        group_posts.assign(day=group_posts["date"].str[:10])
        .groupby("day").size().reset_index(name="Posts")
    )

    if not spread.empty:
        fig = px.line(
            spread, x="day", y="Posts",
            markers=True, title="Claim Spread Over Time"
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("**Supporting and Denying Posts**")
    st.dataframe(
        group_posts[[
            "author", "language", "stance",
            "text", "evidence_quote", "date", "url"
        ]],
        use_container_width=True,
        hide_index=True
    )

    st.markdown("**Potential Duplicate / Coordinated Posts**")

    duplicate_pairs = detect_group_duplicates(selected_group)

    if duplicate_pairs:
        duplicate_df = pd.DataFrame(duplicate_pairs)
        st.dataframe(
            duplicate_df,
            use_container_width=True,
            hide_index=True
        )
        st.caption(
            "Similarity flags are indicators only; they do not prove coordination."
            )
    else:
        st.info("No near-identical posts detected in this group.")

st.divider()

st.subheader("High-Risk Posts")

high_risk_posts = posts[posts["risk_level"].isin(["high", "medium"])]

st.dataframe(
    high_risk_posts[[
        "topic", "author", "text", "risk_level",
        "stance", "date", "url"
    ]],
    use_container_width=True,
    hide_index=True
)

st.divider()

st.subheader("All Posts")

st.dataframe(
    posts[[
        "topic", "author", "language", "main_claim",
        "stance", "sentiment", "risk_level", "date", "url"
    ]],
    use_container_width=True,
    hide_index=True
)



st.divider()
st.subheader("Download PDF Intelligence Report")

report_topic = st.selectbox(
    "Select report topic",
    sorted(posts["topic"].dropna().unique().tolist())
)

if st.button("Generate PDF Report"):
    report_path = generate_pdf_report(report_topic)

    with open(report_path, "rb") as pdf_file:
        pdf_data = pdf_file.read()

    filename = report_topic.replace(" ", "_").replace("&", "and") + "_Report.pdf"

    st.download_button(
        label="Download PDF",
        data=pdf_data,
        file_name=filename,
        mime="application/pdf"
    )
