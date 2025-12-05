import requests
import os
from dotenv import load_dotenv

load_dotenv()

# Invidious trending endpoint (YouTube alternative API)
INVIDIOUS_TRENDING_URL = "https://invidious.projectsegfau.lt/api/v1/trending?region=US"

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"

REVIEW_KEYWORDS = [
    "tech review",
    "unboxing",
    "smart home review",
    "gadget review",
    "laptop review",
    "headphones review",
]


# -----------------------------------
# YOUTUBE TRENDING VIA INVIDIOUS API
# -----------------------------------

def fetch_youtube_trending():
    print("📺 Fetching YouTube Trending (Invidious API)…")
    items = []

    try:
        r = requests.get(INVIDIOUS_TRENDING_URL, timeout=10)
        data = r.json()
    except Exception as e:
        print("❌ Error fetching trending:", e)
        return items

    for v in data:
        items.append({
            "source": "youtube_trending",
            "title": v.get("title"),
            "text": v.get("description"),
            "url": f"https://www.youtube.com/watch?v={v.get('videoId')}",
            "published_at": v.get("published")
        })

    print(f"Trending videos collected: {len(items)}")
    return items


# -----------------------------------
# YOUTUBE REVIEWS (OFFICIAL API)
# -----------------------------------

def fetch_youtube_reviews(max_results=25):
    if not YOUTUBE_API_KEY:
        print("No YOUTUBE_API_KEY — skipping review search.")
        return []

    print("Fetching YouTube product reviews (API)…")

    items = []

    for kw in REVIEW_KEYWORDS:
        params = {
            "part": "snippet",
            "q": kw,
            "maxResults": max_results,
            "type": "video",
            "key": YOUTUBE_API_KEY,
        }

        try:
            r = requests.get(SEARCH_URL, params=params, timeout=10)
            data = r.json()

            for item in data.get("items", []):
                snippet = item["snippet"]
                videoId = item["id"]["videoId"]

                items.append({
                    "source": f"youtube_review:{kw}",
                    "title": snippet["title"],
                    "text": snippet["description"],
                    "url": f"https://www.youtube.com/watch?v={videoId}",
                    "published_at": snippet.get("publishedAt"),
                })

        except Exception as e:
            print(f"Review fetch error for {kw}:", e)

    print(f"YouTube reviews collected: {len(items)}")
    return items


# -----------------------------------
# TEST
# -----------------------------------
if __name__ == "__main__":
    print("\n=== Testing Trending ===")
    trending = fetch_youtube_trending()
    print("Sample:", trending[:3])

    print("\n=== Testing Reviews ===")
    reviews = fetch_youtube_reviews()
    print("Sample:", reviews[:3])
