import feedparser
from datetime import datetime, timezone

GOOGLE_QUERIES = [
    "smart home",
    "consumer electronics",
    "gadgets",
    "robot vacuum",
    "AI tools",
    "wireless earbuds",
]

RSS_FEEDS = [
    "https://techcrunch.com/feed/",
    "https://www.theverge.com/rss/index.xml",
    "https://www.wired.com/feed/rss",
    "https://www.engadget.com/rss.xml",
    "https://www.gsmarena.com/rss-news-reviews.php3",
]

def fetch_google_news_rss():
    print("Fetching Google News RSS…")
    items = []

    for query in GOOGLE_QUERIES:
        url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}"
        feed = feedparser.parse(url)

        for entry in feed.entries:
            items.append({
                "source": "GoogleNews",
                "title": entry.title,
                "text": entry.summary if hasattr(entry, "summary") else entry.title,
                "url": entry.link,
                "published_at": entry.published if hasattr(entry, "published") else None
            })

    print(f"Google News RSS collected: {len(items)}")
    return items


def fetch_rss_feeds():
    print("Fetching RSS feeds (TechCrunch, Verge, Wired…)")
    items = []

    for feed_url in RSS_FEEDS:
        parsed = feedparser.parse(feed_url)

        for entry in parsed.entries:
            items.append({
                "source": feed_url,
                "title": entry.title,
                "text": entry.summary if hasattr(entry, "summary") else entry.title,
                "url": entry.link,
                "published_at": entry.published if hasattr(entry, "published") else None
            })

    print(f"Other RSS sources collected: {len(items)}")
    return items


if __name__ == "__main__":
    test1 = fetch_google_news_rss()
    test2 = fetch_rss_feeds()
    print("Samples:", test1[:2], test2[:2])
