import os
import math
import time
from datetime import datetime, timedelta, timezone
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

# ------------------------------
# IMPORT INGESTION MODULES
# ------------------------------

from ingestion.news_api import fetch_news
from ingestion.reddit_json import fetch_reddit_json
from ingestion.amazon import fetch_amazon_best_sellers
# from ingestion.tiktok import fetch_tiktok_trends
from ingestion.news_rss import fetch_google_news_rss, fetch_rss_feeds
from ingestion.youtube import fetch_youtube_trending, fetch_youtube_reviews



# ------------------------------
# CONFIG
# ------------------------------

CATEGORIES = [
    "technology",
    "gadgets",
    "consumer electronics",
    "AI",
    "smart home",
    "robotics",
]

SUBREDDITS = [
    "technology",
    "gadgets",
    "technews",
    "hardware",
    "Apple",
    "Android",
    "HomeAutomation",
]

BATCH_SIZE = 100  # items per OpenAI batch


# ------------------------------
# OPENAI BATCH PROCESSORS
# ------------------------------

def call_openai_mini(prompt):
    """Send to GPT-4.1-mini with retry logic."""
    for attempt in range(3):
        try:
            resp = client.responses.create(
                model="gpt-4.1-mini",
                input=prompt
            )
            return resp.output_text
        except Exception as e:
            print(f"⚠️ GPT-4.1-mini failed attempt {attempt+1}: {e}")
            time.sleep(2)
    return "ERROR: GPT-4.1-mini failed after retries."


def call_openai_refinement(prompt):
    """Second pass using GPT-4.1 for high-quality analysis."""
    try:
        resp = client.responses.create(
            model="gpt-4.1",
            input=prompt
        )
        return resp.output_text
    except Exception as e:
        return f"ERROR during refinement: {e}"


# ------------------------------
# TREND ANALYSIS PIPELINE
# ------------------------------

def analyze_batched(all_entries):
    titles = [e["title"] for e in all_entries if e["title"]]

    total = len(titles)
    print(f"\n🧩 Total items to analyze: {total}")

    num_batches = math.ceil(total / BATCH_SIZE)
    print(f"📦 Processing in {num_batches} batches of {BATCH_SIZE} each\n")

    batch_summaries = []

    for i in range(num_batches):
        start = i * BATCH_SIZE
        end = start + BATCH_SIZE
        batch_titles = titles[start:end]

        batch_text = "\n".join([f"- {t}" for t in batch_titles])

        mini_prompt = f"""
You are an expert trend classifier.

Analyze the following headlines:

{batch_text}

Extract:
- Key emerging trends
- Categories represented
- Product mentions
- Sentiment direction
- 3–5 short insights

Return a concise summary.
"""

        print(f"⚡ Processing batch {i+1}/{num_batches}...")
        summary = call_openai_mini(mini_prompt)
        batch_summaries.append(summary)

    combined = "\n\n".join(batch_summaries)

    refinement_prompt = f"""
You are a senior market analyst.

Here are summaries from {num_batches} batches of news, Reddit, and Amazon Best Sellers:

{combined}

Create a FINAL TREND REPORT:

1. Identify 10–12 major cross-platform trends.
2. For each trend include:
   - Trend title
   - Why it's rising
   - Market impact
   - Evidence patterns
   - Trend Score (0–100)
   - Whether rising, stable, or cooling
3. End with a 5-line executive summary.

Return a clean, readable report.
"""

    print("\n🧠 Running refinement with GPT-4.1…")
    final_report = call_openai_refinement(refinement_prompt)
    return final_report


# ------------------------------
# MAIN ENGINE
# ------------------------------

def run_trend_engine():
    print("\n🚀 Running Trend Engine…")

    all_entries = []

    # ------------------------------
    # Fetch News
    # ------------------------------
    for cat in CATEGORIES:
        print(f"📰 Fetching News: {cat}")
        news_items = fetch_news(cat)
        for n in news_items:
            all_entries.append({
                "source": n.get("source", {}).get("name"),
                "title": n.get("title"),
                "text": (n.get("title") or "") + "\n\n" + (n.get("description") or ""),
                "url": n.get("url"),
                "published_at": n.get("publishedAt"),
            })

    # ------------------------------
    # Fetch Reddit
    # ------------------------------
    reddit_items = fetch_reddit_json(SUBREDDITS, limit=50)
    all_entries.extend(reddit_items)

    # ------------------------------
    # Fetch Amazon Best Sellers
    # ------------------------------
    amazon_items = fetch_amazon_best_sellers()
    all_entries.extend(amazon_items)

    # tiktok_items = fetch_tiktok_trends()
    # all_entries.extend(tiktok_items)

        # Fetch Google News RSS
    google_rss = fetch_google_news_rss()
    all_entries.extend(google_rss)

    # Fetch other tech RSS sources
    rss_items = fetch_rss_feeds()
    all_entries.extend(rss_items)

    yt_trending = fetch_youtube_trending()
    all_entries.extend(yt_trending)

    yt_reviews = fetch_youtube_reviews()
    all_entries.extend(yt_reviews)


    print(f"\n📦 Total items collected: {len(all_entries)}")

    # ------------------------------
    # Run Trend Analysis
    # ------------------------------

    final_report = analyze_batched(all_entries)

    print("\n====================== FINAL TREND REPORT ======================\n")
    print(final_report)
    print("\n===============================================================\n")

    # Save output
    with open("trend_report_optimized.txt", "w", encoding="utf-8") as f:
        f.write(final_report)

    print("📄 Saved to trend_report_optimized.txt")


if __name__ == "__main__":
    run_trend_engine()
