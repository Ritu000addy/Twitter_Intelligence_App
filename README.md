Twitter/X Intelligence Platform

A multilingual social media intelligence application that collects public X posts, extracts and tracks claims across English, Hindi and Hinglish, analyses stance and risk, identifies potential duplicate or coordinated posts, and generates PDF intelligence reports.


1. Live Application - 

Live app: twitterintelligenceapp-kjjhhwketgzg9uwwfxzinn.streamlit.app
* Username: username
* Password: password


2. Features - 

Data Collection: 

Collects public X posts using the SocialCrawl API.
Supports three predefined topics:

**E20 Petrol**

**UPI Charges**

**EVM and Voting**

- Supports custom topic collection through user-provided search queries.
- Stores post text, author, date, URL, language and engagement counts.
- Uses post IDs and SQLite uniqueness constraints to prevent duplicate records.


AI-Powered Claim Intelligence: 

- Extracts factual claims using Google Gemini (gemini-3.5-flash-lite)
- Normalises Hindi and Hinglish claims into English for cross-language comparison.
- Classifies stance as supports, denies, neutral or unclear.
- Analyses sentiment, risk level and named entities.
Validates evidence quotes against the original post.
- Groups semantically similar claims using multilingual sentence embeddings.
- Generates English claim titles and summaries.
- Tracks claim spread, authors, languages and engagement.
- Detects near-identical posts as potential coordination signals, not proof.
- Uses cached analysis results to avoid unnecessary repeated LLM calls.


Dashboard: 

- Topic filtering and post search.
- Summary metrics and charts.
- Claim group details and risk explanations.
- Supporting and denying posts.
- Claim spread timelines.
- Potential duplicate/coordinated post detection.
- High-risk posts and searchable post records.


PDF Reports:

- Executive summary
- Top claims and source posts
- Claim group analysis
- Claim spread charts
- Supporting and denying post counts
- High-risk posts
- Limitations
- Hindi font rendering support


3. Technology Stack

| Component | Technology |
|---|---|
| Programming language | Python |
| Data collection | SocialCrawl API |
| LLM |  Google Gemini |
| Embeddings  | Sentence Transformers |
| Claim similarity   | Scikit-learn |
| Database  | SQLite |
| Dashboard  | Streamlit |
| Charts  | Plotly, Matplotlib |
| PDF generation  | ReportLab |
| Hosting  | Streamlit Community Cloud |
| Authentication  | Streamlit Secrets |


4. Architecture

SocialCrawl API
      v
Data Collection Module
      v
SQLite Database
      v
LLM Claim Extraction
      v
Multilingual Embeddings
      v
Semantic Claim Grouping
      v
Group Analysis and Duplicate Detection
      +------------------+
      v                  v
Streamlit Dashboard   PDF Reports


5. Project Structure

Twitter_Intelligence_App/
|
|-- backend/
|   |-- collect_data.py
|   |-- database.py
|   |-- import_data.py
|   |-- search.py
|   |-- intelligence/
|       |-- claim_extractor.py
|       |-- claim_grouping.py
|       |-- duplicate_detector.py
|       |-- group_analyzer.py
|       |-- report_generator.py
|
|-- dashboard/
|   |-- app.py
|
|-- data/
|   |-- twitter_intelligence.db
|
|-- reports/
|-- scripts/
|-- assets/
|-- requirements.txt
|-- README.md


6. Local Setup

Requirements: 

- Python 3.12
- Git
- SocialCrawl API key
- Google Gemini API key

Installation:

- Create a virtual environment
- Windows activation of venv
- Install dependencies
- Create .env file in the project root


7. Running the Application

- Collect posts:
```bash
python -m backend.collect_data
```
- Run claim analysis:

python -m scripts.run_analysis

- Group claims:

python -m backend.intelligence.claim_grouping

- Generate PDF reports:

python -m backend.intelligence.report_generator

- Launch dashboard locally:

streamlit run dashboard/app.py


8. Data Collection Method

- The application uses keyword-based X search queries through SocialCrawl.
- Search queries target relevant English, Hindi and Hinglish discussions. Retrieved posts are stored in SQLite. Duplicate post IDs are ignored during subsequent collection runs.
- The application initially collected:

| Topic |  Unique Posts |
|---|---|
| E20 Petrol  | 101 |
| UPI Charges   | 116 |
| EVM and Voting    | 118 |
| Total  | 335 |

- An additional custom-topic collection test was performed for Electric Vehicles.


9. Accuracy and Validation

- Verified collection counts and duplicate prevention.
- Tested English, Hindi and Hinglish claim extraction.
- Compared representative cross-language claim matches.
- Checked unrelated claim examples for separation.
- Tested supporting and denying stance classification.
- Validated evidence quotes against original post text.
- Tested invalid LLM output handling.
- Verified analysis caching.
- Ran an adversarial prompt-injection test successfully.
- Tested claim group timelines and duplicate detection.
- Generated and inspected topic-specific PDF reports.
- Tested the deployed dashboard, login and PDF downloads.


10. Limitations

- Collection coverage depends on API availability, search keywords and platform access.
- Search results do not represent every public post on X.
- LLM extraction, stance classification and risk assessment may contain errors.
- Semantic similarity can occasionally group unrelated claims or separate related claims.
- Claim grouping and summaries are automated and require human review.
- Potential coordination signals do not establish coordinated behaviour.
- The application does not independently determine whether claims are true or false.
- Gemini service availability and rate limits may affect automated summaries.
- New-topic collection depends on appropriate search queries.


11. Responsible Use

This application is designed for social media claim monitoring and research. Its outputs are indicators for further investigation, not verified facts. Human verification and independent evidence are necessary before drawing conclusions.

- Project: Twitter/X Intelligence Platform
- Purpose: Multilingual claim monitoring and intelligence reporting
- Interface: Streamlit Web Application