# #!/usr/bin/env python3
# # trend.py — fixed version with better rate limit handling

# import time
# import random
# import requests
# import pandas as pd
# from textblob import TextBlob
# from pytrends.request import TrendReq

# # -----------------------
# # CONFIG
# # -----------------------

# PRODUCTS = [
#     "smartwatch",
#     "wireless earbuds",
#     "laptop",
#     "gaming chair",
#     "robot vacuum",
#     "fitness tracker",
#     "tablet",
#     "camera"
# ]

# TIMEFRAME = "today 1-m"
# GEO = "DE"
# NEWS_API_KEY = "9f6e6e06bec648a2a2a5bebce1995356"

# CHUNK_SIZE = 3        # REDUCED: Fetch fewer keywords at once
# MAX_ATTEMPTS = 5      # Reduced attempts
# INITIAL_BACKOFF = 60  # INCREASED: Start with longer wait

# NEWS_ENDPOINT = "https://newsapi.org/v2/everything"


# # -----------------------
# # HELPERS
# # -----------------------

# def chunks(lst, n):
#     """Yield successive n-sized chunks."""
#     for i in range(0, len(lst), n):
#         yield lst[i:i + n]


# def safe_fetch_trend_chunk(chunk, attempt_num=0):
#     """
#     Fetch Google Trends for one chunk.
#     Uses exponential backoff with jitter.
#     """
#     try:
#         # Create new instance each time with randomized config
#         py = TrendReq(
#             hl='en-US',
#             tz=360,
#             timeout=(10, 25),  # connection and read timeout
#             retries=0,  # Handle retries ourselves
#             backoff_factor=0.1
#         )
        
#         py.build_payload(chunk, timeframe=TIMEFRAME, geo=GEO)
#         df = py.interest_over_time()

#         if df is None or df.empty:
#             raise ValueError("Empty Google Trends response")

#         if "isPartial" in df.columns:
#             df = df.drop(columns=["isPartial"])

#         print(f"✔ Trends success for {chunk}")
#         return df

#     except Exception as e:
#         print(f"❌ Attempt {attempt_num + 1} failed for {chunk}: {e}")
        
#         if attempt_num >= MAX_ATTEMPTS - 1:
#             print(f"❌ Giving up on {chunk}")
#             return None
        
#         # Exponential backoff with jitter
#         base_delay = INITIAL_BACKOFF * (2 ** attempt_num)
#         jitter = random.uniform(0, 10)
#         delay = base_delay + jitter
        
#         print(f"⏳ Waiting {delay:.1f}s before retry {attempt_num + 2}...")
#         time.sleep(delay)
        
#         return safe_fetch_trend_chunk(chunk, attempt_num + 1)


# def fetch_all_trends(keyword_list, chunk_size=CHUNK_SIZE):
#     """
#     Returns combined DataFrame for all keyword chunks.
#     Adds long delays between chunks.
#     """
#     dfs = []
#     chunk_list = list(chunks(keyword_list, chunk_size))
    
#     print(f"📦 Processing {len(chunk_list)} chunks of {chunk_size} keywords each\n")

#     for i, chunk in enumerate(chunk_list):
#         print(f"🔍 Processing chunk {i+1}/{len(chunk_list)}: {chunk}")
        
#         df = safe_fetch_trend_chunk(chunk)
        
#         if df is not None:
#             dfs.append(df)
        
#         # Long delay between chunks (except after last chunk)
#         if i < len(chunk_list) - 1:
#             delay = random.uniform(45, 75)  # 45-75 seconds between chunks
#             print(f"⏸️  Waiting {delay:.1f}s before next chunk...\n")
#             time.sleep(delay)

#     if not dfs:
#         return None

#     return pd.concat(dfs, axis=1)


# def fetch_news_sentiment(keyword):
#     """Fetch news count + sentiment."""
#     try:
#         params = {
#             "q": keyword,
#             "apiKey": NEWS_API_KEY,
#             "language": "en",
#             "sortBy": "relevancy",
#             "pageSize": 20
#         }
#         r = requests.get(NEWS_ENDPOINT, params=params, timeout=15)
#         data = r.json()

#         if data.get("status") != "ok":
#             print(f"⚠️ NewsAPI issue for {keyword}: {data}")
#             return 0, 0.0

#         articles = data.get("articles", [])
#         titles = [a["title"] for a in articles if a.get("title")]

#         if not titles:
#             return 0, 0.0

#         sentiment = sum(TextBlob(t).sentiment.polarity for t in titles) / len(titles)

#         return len(articles), sentiment

#     except Exception as e:
#         print(f"❌ NewsAPI error for {keyword}: {e}")
#         return 0, 0.0


# # -----------------------
# # MAIN PIPELINE
# # -----------------------

# def main():
#     print("▶ Starting Trend Analyzer...\n")
#     print("⚠️  NOTE: This will take several minutes due to rate limiting.\n")

#     # -----------------------
#     # 1️⃣ Fetch Google Trends
#     # -----------------------
#     print("📊 Fetching Google Trends...")
#     trends = fetch_all_trends(PRODUCTS)

#     if trends is None:
#         print("\n❌ No Google Trends data available.")
#         print("💡 Try again later or reduce PRODUCTS list to 3-4 items.")
#         return

#     # extract last row
#     latest = trends.tail(1).T
#     latest.columns = ["google_trend_score"]

#     # ensure all products exist in index
#     for p in PRODUCTS:
#         if p not in latest.index:
#             latest.loc[p] = {"google_trend_score": 0}

#     # -----------------------
#     # 2️⃣ Fetch News Mentions + Sentiment
#     # -----------------------
#     print("\n📰 Fetching News & Sentiment...")

#     news_counts = {}
#     news_sentiments = {}

#     for p in PRODUCTS:
#         count, sent = fetch_news_sentiment(p)
#         news_counts[p] = count
#         news_sentiments[p] = sent
#         time.sleep(random.uniform(0.5, 1.2))

#     latest["news_mentions"] = latest.index.map(news_counts)
#     latest["news_sentiment"] = latest.index.map(news_sentiments)

#     # -----------------------
#     # 3️⃣ Normalize + Combine
#     # -----------------------
#     df = latest.astype(float)

#     max_trend = df["google_trend_score"].max() or 1
#     max_news = df["news_mentions"].max() or 1

#     df["trend_norm"] = df["google_trend_score"] / max_trend
#     df["news_norm"] = df["news_mentions"] / max_news
#     df["sentiment_norm"] = (df["news_sentiment"] + 1) / 2

#     df["combined_score"] = (
#         df["trend_norm"] * 0.6 +
#         df["news_norm"] * 0.25 +
#         df["sentiment_norm"] * 0.15
#     )

#     # -----------------------
#     # 4️⃣ Output
#     # -----------------------
#     print("\n✅ Final Trend Ranking:\n")
#     print(df.sort_values("combined_score", ascending=False))

#     df.to_csv("trend_results.csv")
#     print("\n📁 Saved trend_results.csv")


# if __name__ == "__main__":
#     main()






#!/usr/bin/env python3
# trend.py — NewsAPI-only test version

import time
import random
import requests
import pandas as pd
from textblob import TextBlob
from pytrends.request import TrendReq # Still imported but not used in this version

# -----------------------
# CONFIG
# -----------------------

PRODUCTS = [
    "smartwatch",
    "wireless earbuds",
    "laptop",
    "gaming chair",
    "robot vacuum",
    "fitness tracker",
    "tablet",
    "camera"
]

TIMEFRAME = "today 1-m"
GEO = "DE"
NEWS_API_KEY = "9f6e6e06bec648a2a2a5bebce1995356"

CHUNK_SIZE = 3        # REDUCED: Fetch fewer keywords at once (Not used in this version)
MAX_ATTEMPTS = 5      # Reduced attempts (Not used in this version)
INITIAL_BACKOFF = 60  # INCREASED: Start with longer wait (Not used in this version)

NEWS_ENDPOINT = "https://newsapi.org/v2/everything"


# -----------------------
# HELPERS (Google Trends functions are kept but ignored in the test pipeline)
# -----------------------

def chunks(lst, n):
    """Yield successive n-sized chunks."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def safe_fetch_trend_chunk(chunk, attempt_num=0):
    """
    Fetch Google Trends for one chunk.
    Uses exponential backoff with jitter.
    """
    try:
        # Create new instance each time with randomized config
        py = TrendReq(
            hl='en-US',
            tz=360,
            timeout=(10, 25),  # connection and read timeout
            retries=0,  # Handle retries ourselves
            backoff_factor=0.1
        )
        
        py.build_payload(chunk, timeframe=TIMEFRAME, geo=GEO)
        df = py.interest_over_time()

        if df is None or df.empty:
            raise ValueError("Empty Google Trends response")

        if "isPartial" in df.columns:
            df = df.drop(columns=["isPartial"])

        print(f"✔ Trends success for {chunk}")
        return df

    except Exception as e:
        print(f"❌ Attempt {attempt_num + 1} failed for {chunk}: {e}")
        
        if attempt_num >= MAX_ATTEMPTS - 1:
            print(f"❌ Giving up on {chunk}")
            return None
        
        # Exponential backoff with jitter
        base_delay = INITIAL_BACKOFF * (2 ** attempt_num)
        jitter = random.uniform(0, 10)
        delay = base_delay + jitter
        
        print(f"⏳ Waiting {delay:.1f}s before retry {attempt_num + 2}...")
        time.sleep(delay)
        
        return safe_fetch_trend_chunk(chunk, attempt_num + 1)


def fetch_all_trends(keyword_list, chunk_size=CHUNK_SIZE):
    """
    Returns combined DataFrame for all keyword chunks.
    Adds long delays between chunks.
    """
    dfs = []
    chunk_list = list(chunks(keyword_list, chunk_size))
    
    print(f"📦 Processing {len(chunk_list)} chunks of {chunk_size} keywords each\n")

    for i, chunk in enumerate(chunk_list):
        print(f"🔍 Processing chunk {i+1}/{len(chunk_list)}: {chunk}")
        
        df = safe_fetch_trend_chunk(chunk)
        
        if df is not None:
            dfs.append(df)
        
        # Long delay between chunks (except after last chunk)
        if i < len(chunk_list) - 1:
            delay = random.uniform(45, 75)  # 45-75 seconds between chunks
            print(f"⏸️  Waiting {delay:.1f}s before next chunk...\n")
            time.sleep(delay)

    if not dfs:
        return None

    return pd.concat(dfs, axis=1)


def fetch_news_sentiment(keyword):
    """Fetch news count + sentiment."""
    try:
        params = {
            "q": keyword,
            "apiKey": NEWS_API_KEY,
            "language": "en",
            "sortBy": "relevancy",
            "pageSize": 20
        }
        r = requests.get(NEWS_ENDPOINT, params=params, timeout=15)
        data = r.json()

        if data.get("status") != "ok":
            print(f"⚠️ NewsAPI issue for {keyword}: {data}")
            return 0, 0.0

        articles = data.get("articles", [])
        titles = [a["title"] for a in articles if a.get("title")]

        if not titles:
            return 0, 0.0

        sentiment = sum(TextBlob(t).sentiment.polarity for t in titles) / len(titles)

        return len(articles), sentiment

    except Exception as e:
        print(f"❌ NewsAPI error for {keyword}: {e}")
        return 0, 0.0


# -----------------------
# NEWSAPI-ONLY TEST PIPELINE (The new main logic)
# -----------------------

def test_news_api_only():
    print("▶ Starting NewsAPI-Only Test...\n")
    print(f"Testing {len(PRODUCTS)} products: {', '.join(PRODUCTS)}")
    print("----------------------------------------------------------")

    results = {}
    
    # Iterate through products and call the NewsAPI function
    for p in PRODUCTS:
        print(f"🔎 Querying news for: {p}")
        
        # Call the existing NewsAPI function
        count, sent = fetch_news_sentiment(p)
        
        results[p] = {"news_mentions": count, "news_sentiment": f"{sent:.4f}"}
        
        print(f"   -> Mentions: {count}, Sentiment: {sent:.4f}")
        # Add a short, random delay to be polite to the API
        time.sleep(random.uniform(0.5, 1.2))

    # Compile and output results
    df = pd.DataFrame.from_dict(results, orient='index')
    df['news_mentions'] = df['news_mentions'].astype(int) # Convert count back to integer for sorting

    print("\n✅ Final NewsAPI Results:\n")
    print(df.sort_values("news_mentions", ascending=False))
    
    # Save a CSV of the news results
    df.to_csv("news_only_results.csv")
    print("\n📁 Saved news_only_results.csv")


if __name__ == "__main__":
    # This line runs the NewsAPI-only test function.
    test_news_api_only()