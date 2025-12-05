from playwright.sync_api import sync_playwright

TIKTOK_TAGS = [
    "gadgets",
    "smarthome",
    "tech",
    "robotvacuum",
    "earbuds",
]


def fetch_tiktok_trends():
    print("🎵 Launching TikTok browser scraper via Playwright…")
    items = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/120.0.0.0 Safari/537.36",
            locale="en-US"
        )
        page = context.new_page()

        for tag in TIKTOK_TAGS:
            print(f"\n🔍 Fetching TikTok tag: #{tag}…")

            url = f"https://www.tiktok.com/tag/{tag}"

            try:
                page.goto(url, timeout=60000)
                page.wait_for_timeout(4000)

                # Extract all video descriptions
                posts = page.query_selector_all("div[data-e2e='feed-item-desc']")

                for post in posts:
                    text = post.inner_text().strip()
                    if text:
                        items.append({
                            "source": f"tiktok/#{tag}",
                            "title": text,
                            "text": text,
                            "url": None,
                            "published_at": None
                        })

                print(f"✔ Extracted {len(posts)} posts from #{tag}")

            except Exception as e:
                print(f"❌ Error scraping #{tag}: {e}")

        browser.close()

    print(f"\n📦 TOTAL TikTok items collected: {len(items)}")
    return items


# Standalone test
if __name__ == "__main__":
    results = fetch_tiktok_trends()
    print("\nSample:", results[:5])
