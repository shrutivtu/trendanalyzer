import requests
from datetime import datetime

SEMRUSH_TRENDS_URL = (
    "https://trends-production.api.semrush.com/shopping/trends?country=us"
)

def fetch_google_shopping_trends():
    print("🛒 Fetching Shopping Trends via SEMrush…")

    items = []

    try:
        r = requests.get(SEMRUSH_TRENDS_URL, timeout=10)
        data = r.json()
    except Exception as e:
        print("❌ Error fetching Shopping Trends:", e)
        return items

    for t in data.get("trends", []):
        items.append({
            "source": "google_shopping_trends",
            "title": t.get("query"),
            "text": f"Category: {t.get('category')} | Growth: {t.get('growth')}% | Movement: {t.get('movement')}",
            "url": None,
            "published_at": datetime.utcnow().isoformat()
        })

    print(f"📦 Shopping trend items collected: {len(items)}")
    return items


if __name__ == "__main__":
    print(fetch_google_shopping_trends()[:5])
