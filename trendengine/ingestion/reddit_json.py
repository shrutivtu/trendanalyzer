import requests
from datetime import datetime, timezone

def fetch_reddit_json(subreddits, limit=50):
    all_posts = []
    headers = {"User-Agent": "trend-agent/1.0"}

    for sub in subreddits:
        print(f"Fetching Reddit: r/{sub}")
        url = f"https://www.reddit.com/r/{sub}/hot.json?limit={limit}"

        try:
            r = requests.get(url, headers=headers, timeout=10)
            data = r.json()

            for child in data["data"]["children"]:
                p = child["data"]

                post = {
                    "source": f"reddit/{sub}",
                    "title": p["title"],
                    "text": (p.get("selftext") or p["title"]),
                    "url": "https://www.reddit.com" + p["permalink"],
                    "published_at": datetime.fromtimestamp(
                        p["created_utc"], tz=timezone.utc
                    ).isoformat(),
                }
                all_posts.append(post)

        except Exception as e:
            print(f"Error fetching r/{sub}: {e}")

    return all_posts
