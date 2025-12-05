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
# GEMINI CLIENT (imported from llm/)
# ------------------------------
from llm.gemini_client import gemini_pro  # <-- correct import


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
    """Use GPT-4.1-mini for cheap batched classification."""
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

    return "ERROR: GPT-4.1-mini failed."


# ------------------------------
# GPT-4 REFINEMENT (fallback)
# ------------------------------

def call_openai_refinement(prompt):
    """Use GPT-4.1 for refinement when context is small."""
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
    - Under 20k characters → GPT-4.1 (fast + cheap)
    - Over 20k characters  → Gemini 1.5 Pro Latest (deep analysis)
    """
    length = len(prompt)

    if length < 20000:
        print(" Auto-select: Using GPT-4.1 (prompt is small)…")
        return call_openai_refinement(prompt)

    # Change the model argument here:
    print("Auto-select: Using gemini-2.5-pro (large prompt)…")
    # Change: model="gemini-1.5-pro-latest"
    return gemini_pro(prompt, model="gemini-2.5-pro")



# ------------------------------
# TREND ANALYSIS PIPELINE
# ------------------------------

def analyze_batched(all_entries):
    titles = [e["title"] for e in all_entries if e["title"]]

    total = len(titles)
    print(f"\n Total items to analyze: {total}")

    num_batches = math.ceil(total / BATCH_SIZE)
    print(f"Processing {num_batches} batches of {BATCH_SIZE} items\n")

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

Return a concise summary.
"""

        print(f"⚡ Batch {i+1}/{num_batches}…")
        summary = call_openai_mini(mini_prompt)
        batch_summaries.append(summary)

    combined = "\n\n".join(batch_summaries)

    refinement_prompt = f"""
You are a senior market analyst.

Here are summaries from {num_batches} batches (news, Reddit, Amazon, RSS, YouTube):

{combined}

Create a FINAL TREND REPORT:

1. Identify 10–12 major cross-platform trends.
2. For each trend:
   - Trend Title
   - Why it is rising
   - Market impact
   - Supporting evidence
   - Trend Score (0–100)
   - Label (Rising / Stable / Cooling)
3. End with a powerful executive summary.

Return clean, structured output.
"""

    print("\n Running FINAL refinement…")
    return final_llm_analysis(refinement_prompt)


# ------------------------------
# MAIN ENGINE
# ------------------------------

def run_trend_engine():
    print("\n🚀 Running Trend Engine…")
    all_entries = []

    # News
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

    # Reddit
    all_entries.extend(fetch_reddit_json(SUBREDDITS, limit=50))

    # Amazon Best Sellers
    all_entries.extend(fetch_amazon_best_sellers())

    # Google News RSS
    all_entries.extend(fetch_google_news_rss())

    # Tech RSS feeds
    all_entries.extend(fetch_rss_feeds())

    # YouTube trending
    all_entries.extend(fetch_youtube_trending())

    # YouTube reviews
    all_entries.extend(fetch_youtube_reviews())

    print(f"\n Total collected items: {len(all_entries)}")

    final_report = analyze_batched(all_entries)

    print("\n====================== FINAL TREND REPORT ======================\n")
    print(final_report)
    print("\n===============================================================\n")

    with open("trend_report_optimized.txt", "w", encoding="utf-8") as f:
        f.write(final_report)

    print("Saved to trend_report_optimized.txt")


if __name__ == "__main__":
    run_trend_engine()
