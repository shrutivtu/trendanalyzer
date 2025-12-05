import requests
import os
from dotenv import load_dotenv

load_dotenv()

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

def fetch_youtube_trending(region="DE"):
    """
    Fetch trending videos from YouTube using YouTube Data API.
    
    Args:
        region: ISO 3166-1 alpha-2 country code (default: DE for Germany)
    """
    print(f"📺 Fetching YouTube Trending for {region}…")
    items = []
    
    if not YOUTUBE_API_KEY:
        print("❌ No YOUTUBE_API_KEY available")
        return items
    
    try:
        # YouTube Data API "most popular" videos (trending)
        params = {
            "part": "snippet,contentDetails",
            "chart": "mostPopular",
            "regionCode": region,
            "maxResults": 50,
            "key": YOUTUBE_API_KEY,
        }
        
        url = "https://www.googleapis.com/youtube/v3/videos"
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        
        if "error" in data:
            print(f"❌ YouTube API Error: {data['error'].get('message', 'Unknown error')}")
            return items
        
        for item in data.get("items", []):
            snippet = item.get("snippet", {})
            video_id = item.get("id")
            
            items.append({
                "source": "youtube_trending",
                "title": snippet.get("title"),
                "text": snippet.get("description"),
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "published_at": snippet.get("publishedAt")
            })
        
        print(f"✅ Successfully fetched from YouTube Data API")
        print(f"Trending videos collected: {len(items)}")
        return items
        
    except Exception as e:
        print(f"❌ YouTube Data API failed: {e}")
    
    return items


# -----------------------------------
# YOUTUBE REVIEWS (OFFICIAL API)
# -----------------------------------

def fetch_youtube_reviews(max_results=25):
    """
    Fetch YouTube reviews using YouTube Data API.
    
    Args:
        max_results: Maximum results per keyword
    """
    if not YOUTUBE_API_KEY:
        print("❌ No YOUTUBE_API_KEY — skipping review search.")
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
            print(f"  Searching for: {kw}")
            r = requests.get(SEARCH_URL, params=params, timeout=10)
            r.raise_for_status()
            data = r.json()
            
            # Check for API errors
            if "error" in data:
                error_msg = data["error"].get("message", "Unknown error")
                error_code = data["error"].get("code", "N/A")
                print(f"  ❌ API Error ({error_code}): {error_msg}")
                continue

            result_count = len(data.get("items", []))
            print(f"  Found {result_count} videos for '{kw}'")

            for item in data.get("items", []):
                snippet = item.get("snippet", {})
                video_id = item.get("id", {}).get("videoId")
                
                if not video_id:
                    continue

                items.append({
                    "source": f"youtube_review:{kw}",
                    "title": snippet.get("title"),
                    "text": snippet.get("description"),
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "published_at": snippet.get("publishedAt"),
                })

        except requests.exceptions.HTTPError as e:
            print(f"  ❌ HTTP Error for '{kw}': {e}")
        except Exception as e:
            print(f"  ❌ Error for '{kw}': {e}")

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
