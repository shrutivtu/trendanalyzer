import os
import requests
from dotenv import load_dotenv

load_dotenv()

PRODUCT_HUNT_API_KEY = os.getenv("PRODUCT_HUNT_API_KEY")

GRAPHQL_URL = "https://api.producthunt.com/v2/api/graphql"

# SAFE GraphQL query (always supported)
QUERY = """
query {
  posts(first: 30, order: VOTES) {
    edges {
      node {
        name
        tagline
        url
        votesCount
        createdAt
      }
    }
  }
}
"""


def fetch_product_hunt():
    print("Fetching Product Hunt trending products…")

    if not PRODUCT_HUNT_API_KEY:
        print("PRODUCT_HUNT_API_KEY is missing in .env")
        return []

    headers = {
        "Authorization": f"Bearer {PRODUCT_HUNT_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    # --------------------------
    # Perform the API request
    # --------------------------
    try:
        response = requests.post(
            GRAPHQL_URL,
            json={"query": QUERY},
            headers=headers,
            timeout=15
        )
    except Exception as e:
        print(f"Network error fetching Product Hunt: {e}")
        return []

    # --------------------------
    # Debug: show raw response text
    # --------------------------
    print("\n----- RAW RESPONSE -----")
    print(response.text)
    print("----- END RAW RESPONSE -----\n")

    # --------------------------
    # Try parsing JSON safely
    # --------------------------
    try:
        data = response.json()
    except Exception as e:
        print(f"Could not decode JSON: {e}")
        return []

    # If Product Hunt sent an error message
    if "errors" in data:
        print("Product Hunt returned errors:")
        print(data["errors"])
        return []

    posts_data = (
        data.get("data", {})
            .get("posts", {})
            .get("edges", [])
    )

    items = []

    for edge in posts_data:
        node = edge.get("node", {})
        if not node:
            continue

        items.append({
            "source": "producthunt",
            "title": node.get("name"),
            "text": node.get("tagline"),
            "url": node.get("url"),
            "published_at": node.get("createdAt"),
        })

    print(f"Product Hunt items collected: {len(items)}")
    return items


# Standalone test
if __name__ == "__main__":
    results = fetch_product_hunt()
    print("\nSample:", results[:3])
