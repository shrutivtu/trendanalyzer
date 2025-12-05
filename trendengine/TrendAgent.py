import os
import math
import time
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ------------------------------
# LLM CONFIG
# ------------------------------

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not OPENAI_API_KEY:
    print("Missing OPENAI_API_KEY in .env")
if not GEMINI_API_KEY:
    print("Missing GEMINI_API_KEY in .env")

# ------------------------------
# OPENAI CLIENT
# ------------------------------
from openai import OpenAI
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# ------------------------------
# GEMINI CLIENT
# ------------------------------
from llm.gemini_client import gemini_pro   # your working gemini wrapper


# ------------------------------
# INGESTION SOURCES
# ------------------------------

from ingestion.news_api import fetch_news
from ingestion.reddit_json import fetch_reddit_json
from ingestion.amazon import fetch_amazon_best_sellers
from ingestion.news_rss import fetch_google_news_rss, fetch_rss_feeds
from ingestion.youtube import fetch_youtube_trending, fetch_youtube_reviews


# ------------------------------
# CONFIG
# ------------------------------

CATEGORIES = [
    "technology", "gadgets", "consumer electronics",
    "AI", "smart home", "robotics"
]

SUBREDDITS = [
    "technology", "gadgets", "technews",
    "hardware", "Apple", "Android", "HomeAutomation"
]

BATCH_SIZE = 100


# ------------------------------
# OPENAI MINI BATCH PROCESSOR
# ------------------------------

def call_openai_mini(prompt):
    """Use GPT-4.1-mini for affordable, fast headline grouping."""
    for attempt in range(3):
        try:
            resp = openai_client.responses.create(
                model="gpt-4.1-mini",
                input=prompt
            )
            return resp.output_text
        except Exception as e:
            print(f"⚠️ GPT-4.1-mini failed attempt {attempt+1}: {e}")
            time.sleep(2)
    return "ERROR: GPT-4.1-mini failed after 3 attempts."


# ------------------------------
# GPT-4.1 REFINEMENT (used only for short prompts)
# ------------------------------

def call_openai_refinement(prompt):
    try:
        resp = openai_client.responses.create(
            model="gpt-4.1",
            input=prompt
        )
        return resp.output_text
    except Exception as e:
        return f"GPT-4.1 refinement error: {e}"


# ------------------------------
# HYBRID MODEL SELECTION LOGIC
# ------------------------------

def final_llm_analysis(prompt):
    """
    AUTO MODEL SELECTION:
    - Under 20k chars → GPT-4.1
    - Over 20k chars  → Gemini-2.5-Pro (long-context)
    """
    length = len(prompt)

    if length < 20000:
        print("✨ Using GPT-4.1 (prompt is small)…")
        return call_openai_refinement(prompt)

    print("Using Gemini-2.5-Pro for long-context final analysis…")
    return gemini_pro(prompt, model="gemini-2.5-pro")


# ------------------------------
# TREND ANALYSIS PIPELINE
# ------------------------------

def analyze_batched(all_entries):
    titles = [e["title"] for e in all_entries if e["title"]]

    total = len(titles)
    print(f"\n🧩 Total items to analyze: {total}")

    num_batches = math.ceil(total / BATCH_SIZE)
    print(f"Processing {num_batches} batches of {BATCH_SIZE} items...\n")

    batch_summaries = []

    for i in range(num_batches):
        batch_titles = titles[i * BATCH_SIZE : (i+1) * BATCH_SIZE]
        batch_text = "\n".join([f"- {t}" for t in batch_titles])

        mini_prompt = f"""
You are an expert trend classifier.

Analyze these headlines:

{batch_text}

Extract:
- Key emerging trends
- Categories
- Product mentions
- Sentiment direction
- 3–5 actionable insights

Return a tight summary. No fluff.
"""

        print(f"⚡ Batch {i+1}/{num_batches}…")
        summary = call_openai_mini(mini_prompt)
        batch_summaries.append(summary)

    combined = "\n\n".join(batch_summaries)

    # ------------------------------
    # FINAL HACKATHON-OPTIMIZED PROMPT
    # ------------------------------

    refinement_prompt = f"""
You are a senior market analyst preparing a professional trend intelligence brief
for a major European consumer electronics retailer (MediaMarkt/Saturn style).

The date today is **December 5, 2025**.
Always use THIS date in the report header.

Use the insights below to generate a highly structured, retail-focused report:

{combined}

=========================
### FINAL TREND REPORT TEMPLATE
=========================

### TO: Retail Strategy & Merchandising Leadership
### FROM: Senior Consumer Electronics & Retail Trend Analyst
### DATE: December 5, 2025
### SUBJECT: Final Q4 2025 Trend Report — AI, Automation & Consumer Electronics Momentum

----------------------------------
### **SECTION 1 — EXECUTIVE SUMMARY (5–7 lines)**
Provide a crisp, strategic overview of the highest-impact forces shaping consumer electronics demand.
Emphasize cross-platform convergence (news + Reddit + Amazon + YouTube + RSS).

----------------------------------
### **SECTION 2 — TOP 10–12 CROSS-PLATFORM TRENDS**
For each trend, include:

**Trend Title (bold, 3–6 words)**
- Why It Is Rising  
- Market Impact (EU retail context preferred)  
- Evidence Snapshot (1–2 bullets from any platforms)  
- Trend Score (0–100)  
- Status (Rising / Stable / Cooling)

Keep each trend short, sharp, and retailer-actionable.

----------------------------------
### **SECTION 3 — RETAIL ACTION RECOMMENDATIONS (6–8 bullets)**
Concrete steps MediaMarkt/Saturn could execute:
- assortment  
- merchandising  
- promotions  
- pricing  
- online/offline experience  
- experimental categories  

----------------------------------
### STYLE RULES:
- No outdated years (always December 2025).
- No long paragraphs—make everything digestible.
- Use real-sounding business language.
- Avoid generic AI fluff.
----------------------------------

Generate the full finalized report.
"""

    print("\n🧠 Running FINAL refinement…")
    return final_llm_analysis(refinement_prompt)


# ------------------------------
# MAIN ENGINE
# ------------------------------

def run_trend_engine():
    print("\n🚀 Running Trend Engine…")
    all_entries = []

    # 1 — NEWS API
    for cat in CATEGORIES:
        print(f"Fetching News: {cat}")
        for n in fetch_news(cat):
            all_entries.append({
                "source": n.get("source", {}).get("name"),
                "title": n.get("title"),
                "text": f"{n.get('title')}\n\n{n.get('description')}",
                "url": n.get("url"),
                "published_at": n.get("publishedAt"),
            })

    # 2 — Reddit
    all_entries.extend(fetch_reddit_json(SUBREDDITS, limit=50))

    # 3 — Amazon Best Sellers
    all_entries.extend(fetch_amazon_best_sellers())

    # 4 — Google News RSS
    all_entries.extend(fetch_google_news_rss())

    # 5 — Tech RSS Feeds
    all_entries.extend(fetch_rss_feeds())

    # 6 — YouTube Trending
    all_entries.extend(fetch_youtube_trending())

    # 7 — YouTube Reviews
    all_entries.extend(fetch_youtube_reviews())

    print(f"\n📦 Total collected items: {len(all_entries)}")

    # Run analysis
    final_report = analyze_batched(all_entries)

    print("\n====================== FINAL TREND REPORT ======================\n")
    print(final_report)
    print("\n===============================================================\n")

    with open("trend_report_optimized.txt", "w", encoding="utf-8") as f:
        f.write(final_report)

    print("Saved to trend_report_optimized.txt")


if __name__ == "__main__":
    run_trend_engine()
