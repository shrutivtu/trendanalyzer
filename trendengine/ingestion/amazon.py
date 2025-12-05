import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

AMAZON_BEST_SELLERS_URL = "https://www.amazon.com/Best-Sellers-Electronics/zgbs/electronics"

def fetch_amazon_best_sellers():
    print("🔍 Fetching Amazon Best Sellers")

    try:
        response = requests.get(AMAZON_BEST_SELLERS_URL, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
    except Exception as e:
        print(f"❌ Error fetching Amazon: {e}")
        return []

    items = []
    product_blocks = soup.select(".zg-grid-general-faceout")

    for block in product_blocks:
        # Title
        title_tag = block.select_one(".p13n-sc-truncate-desktop-type2") or block.select_one("img")
        title = None
        if title_tag:
            title = title_tag.get("alt") or title_tag.text.strip()

        if not title:
            continue

        # Link
        link_tag = block.select_one("a.a-link-normal")
        link = "https://www.amazon.com" + link_tag["href"] if link_tag else None

        # Best sellers rank
        rank_tag = block.select_one(".zg-bdg-text")
        rank = rank_tag.text.strip() if rank_tag else None

        items.append({
            "source": "amazon",
            "title": title,
            "text": f"{title} (Amazon Best Seller Rank: {rank})",
            "url": link,
            "published_at": None,
        })

    print(f"📦 Amazon products scraped: {len(items)}")
    return items
