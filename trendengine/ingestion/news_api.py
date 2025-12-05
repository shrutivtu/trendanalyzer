import requests
from datetime import datetime, timedelta
import os

NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
DAYS_BACK = 1
NEWS_PAGE_SIZE = 30

def fetch_news(category):
    url = (
        "https://newsapi.org/v2/everything?"
        f"q={category}&from={(datetime.utcnow() - timedelta(days=DAYS_BACK)).date()}&"
        f"sortBy=publishedAt&language=en&pageSize={NEWS_PAGE_SIZE}&apiKey={NEWSAPI_KEY}"
    )

    try:
        r = requests.get(url)
        data = r.json()
        return data.get("articles", [])
    except Exception as e:
        print(f"Error fetching news for {category}: {e}")
        return []
