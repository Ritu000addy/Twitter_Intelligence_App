import json
import sqlite3
import pandas as pd

from io import BytesIO
import matplotlib.pyplot as plt

import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, PageBreak, Image
)
from reportlab.lib.units import inch

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from backend.database import DB_NAME, get_connection


def load_topic_data(topic):
    conn = sqlite3.connect(DB_NAME)

    query = """
        SELECT p.*, a.result_json
        FROM posts p
        LEFT JOIN post_analyses a
        ON p.post_id = a.post_id
        WHERE p.topic = ?
    """

    df = pd.read_sql_query(query, conn, params=(topic,))
    conn.close()

    analyses = []

    for value in df["result_json"]:
        try:
            analyses.append(json.loads(value) if value else {})
        except (json.JSONDecodeError, TypeError):
            analyses.append({})

    df["main_claim"] = [a.get("main_claim") for a in analyses]
    df["stance"] = [a.get("stance") for a in analyses]
    df["risk_level"] = [a.get("risk_level") for a in analyses]
    df["language"] = [a.get("language") for a in analyses]
    df["evidence_quote"] = [a.get("evidence_quote") for a in analyses]

    return df


def create_topic_summary(topic):
    df = load_topic_data(topic)

    return {
        "topic": topic,
        "total_posts": len(df),
        "analysed_posts": int(df["result_json"].notna().sum()),
        "claims": int(df["main_claim"].notna().sum()),
        "high_risk_posts": int(
            (df["risk_level"] == "high").sum()
        ),
        "supporting_posts": int(
            (df["stance"] == "supports").sum()
        ),
        "denying_posts": int(
            (df["stance"] == "denies").sum()
        ),
        "languages": sorted(
            df["language"].dropna().unique().tolist()
        )
    }



def load_topic_claim_groups(topic):
    conn = sqlite3.connect(DB_NAME)

    groups = pd.read_sql_query("""
        SELECT *
        FROM claim_groups
        WHERE topic = ?
        ORDER BY total_posts DESC
    """, conn, params=(topic,))

    conn.close()
    return groups


def create_spread_chart(group_id):
    conn = sqlite3.connect(DB_NAME)

    data = pd.read_sql_query("""
        SELECT p.date, a.result_json
        FROM posts p
        JOIN post_claim_groups pcg ON p.post_id = pcg.post_id
        LEFT JOIN post_analyses a ON p.post_id = a.post_id
        WHERE pcg.group_id = ?
    """, conn, params=(group_id,))

    conn.close()

    if data.empty:
        return None

    data["day"] = pd.to_datetime(
        data["date"], errors="coerce"
    ).dt.date

    data = data.dropna(subset=["day"])

    if data.empty:
        return None

    stances = []
    for value in data["result_json"]:
        try:
            result = json.loads(value) if value else {}
        except (json.JSONDecodeError, TypeError):
            result = {}
        stances.append(result.get("stance", "unclear"))

    data["stance"] = stances

    chart_data = (
        data.groupby(["day", "stance"])
        .size()
        .unstack(fill_value=0)
    )

    fig, ax = plt.subplots(figsize=(8, 3.5))
    chart_data.plot(kind="line", marker="o", ax=ax)

    ax.set_title(f"Claim Group {group_id} - Spread Over Time")
    ax.set_xlabel("Date")
    ax.set_ylabel("Number of Posts")
    ax.grid(True, alpha=0.3)
    fig.autofmt_xdate()
    fig.tight_layout()

    image_buffer = BytesIO()
    fig.savefig(image_buffer, format="png", dpi=150)
    plt.close(fig)
    image_buffer.seek(0)

    return image_buffer



def generate_pdf_report(topic):
    df = load_topic_data(topic)
    summary = create_topic_summary(topic)

    os.makedirs("reports", exist_ok=True)

    filename = topic.replace(" ", "_").replace("&", "and") + "_Report.pdf"
    filepath = os.path.join("reports", filename)

    doc = SimpleDocTemplate(filepath, pagesize=A4)
    styles = getSampleStyleSheet()
    font_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "assets",
        "Nirmala.ttc"
    )

    pdfmetrics.registerFont(
        TTFont("Nirmala", font_path, subfontIndex=0)
    )

    for style in styles.byName.values():
        style.fontName = "Nirmala"
    
    story = []

    story.append(Paragraph(f"{topic} - Intelligence Report", styles["Title"]))
    story.append(Spacer(1, 0.25 * inch))

    story.append(Paragraph("Executive Summary", styles["Heading1"]))

    summary_data = [
        ["Metric", "Value"],
        ["Collected Posts", summary["total_posts"]],
        ["Analysed Posts", summary["analysed_posts"]],
        ["Extracted Claims", summary["claims"]],
        ["High-Risk Posts", summary["high_risk_posts"]],
        ["Supporting Posts", summary["supporting_posts"]],
        ["Denying Posts", summary["denying_posts"]],
        ["Languages", ", ".join(summary["languages"])],
    ]

    table = Table(summary_data, colWidths=[2.5 * inch, 3 * inch])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("PADDING", (0, 0), (-1, -1), 7),
    ]))
    story.append(table)
    story.append(Spacer(1, 0.3 * inch))

    story.append(Paragraph("Top Claims", styles["Heading1"]))

    top_claims = (
        df[df["main_claim"].notna()]
        .groupby("main_claim")
        .size()
        .sort_values(ascending=False)
        .head(10)
    )

    for claim, count in top_claims.items():
        story.append(Paragraph(
            f"<b>{claim} ({count} posts)</b>",
            styles["BodyText"]
        ))
        source_posts = df[df["main_claim"] == claim].head(3)

        for _, post in source_posts.iterrows():
            story.append(Paragraph(
                f"Author: {post['author'] or 'Unknown'} | "
                f"Date: {post['date'] or 'Unknown'}",
                styles["BodyText"]
            ))

            story.append(Paragraph(
                str(post["text"])[:500],
                styles["BodyText"]
            ))

            if post["url"]:
                story.append(Paragraph(
                    f"Source: {post['url']}",
                    styles["BodyText"]
                ))

            story.append(Spacer(1, 5))

        story.append(Spacer(1, 10))  

    story.append(Paragraph("Claim Group Analysis", styles["Heading1"]))

    claim_groups = load_topic_claim_groups(topic)

    if claim_groups.empty:
        story.append(Paragraph(
            "No multi-post claim groups available.",
            styles["BodyText"]
        ))

    for _, group in claim_groups.head(10).iterrows():
        story.append(Paragraph(
            f"Group {group['group_id']}: {group['claim_title']}",
            styles["Heading2"]
        ))

        story.append(Paragraph(
            f"Posts: {group['total_posts']} | "
            f"Authors: {group['total_authors']} | "
            f"Languages: {group['total_languages']} | "
            f"Engagement: {group['total_engagement']} | "
            f"Risk: {group['risk_level']}",
            styles["BodyText"]
        ))

        conn = sqlite3.connect(DB_NAME)
        group_data = pd.read_sql_query("""
            SELECT a.result_json
            FROM posts p
            JOIN post_claim_groups pcg ON p.post_id = pcg.post_id
            LEFT JOIN post_analyses a ON p.post_id = a.post_id
            WHERE pcg.group_id = ?
        """, conn, params=(int(group["group_id"]),))
        conn.close()

        support_count = 0
        deny_count = 0

        for value in group_data["result_json"]:
            try:
                result = json.loads(value) if value else {}
            except (json.JSONDecodeError, TypeError):
                result = {}

            if result.get("stance") == "supports":
                support_count += 1
            elif result.get("stance") == "denies":
                deny_count += 1

        story.append(Paragraph(
            f"Supporting: {support_count} | Denying: {deny_count}",
            styles["BodyText"]
        ))

        chart = create_spread_chart(int(group["group_id"]))

        if chart:
            story.append(Spacer(1, 8))
            story.append(Image(chart, width=6.2 * inch, height=2.7 * inch))

        story.append(Spacer(1, 15))


    story.append(Paragraph("High-Risk Posts", styles["Heading1"]))

    risky = df[df["risk_level"].isin(["high", "medium"])].head(20)

    for _, post in risky.iterrows():
        story.append(Paragraph(
            f"<b>Risk:</b> {post['risk_level']} | "
            f"<b>Author:</b> {post['author'] or 'Unknown'}",
            styles["BodyText"]
        ))
        story.append(Paragraph(
            str(post["text"])[:1000],
            styles["BodyText"]
        ))
        if post["url"]:
            story.append(Paragraph(
                f"Source: {post['url']}",
                styles["BodyText"]
            ))
        story.append(Spacer(1, 8))

    story.append(Paragraph("Supporting vs Denying Posts", styles["Heading1"]))

    for stance in ["supports", "denies"]:
        count = int((df["stance"] == stance).sum())
        story.append(Paragraph(
            f"{stance.title()}: {count} posts",
            styles["BodyText"]
        ))

    story.append(Paragraph("Limitations", styles["Heading1"]))
    story.append(Paragraph(
        "Automated claim extraction, grouping and risk classification "
        "may contain errors. Similarity and stance do not establish "
        "whether a claim is true or false. Human verification and "
        "independent evidence are required.",
        styles["BodyText"]
    ))

    doc.build(story)

    print(f"PDF report generated: {filepath}")
    return filepath



if __name__ == "__main__":
    topics = ["E20 Petrol", "UPI Charges", "EVM and Voting"]

    for topic in topics:
        print(create_topic_summary(topic))
        generate_pdf_report(topic)