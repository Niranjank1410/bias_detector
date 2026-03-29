# backend/fetcher/rss_fetcher.py

"""
Fetches articles from rss feeds.

RSS is an XML format that most news sites publish. Its great for sources
not available on NewsAPI, and it often gives more articles per source.
feedparser handles the XML complexity and gives clean Python dicts.
"""

import feedparser
from datetime import datetime
import time

def fetch_rss_feed(source_name: str, rss_url: str) -> list[dict]:
    """
    Fetches and parses a single RSS feed.

    Args:
        source_name: Human-readable name (e.g. "BBC News")
        rss_url: The RSS feed URL

    Returns:
        List of article dicts in our normalised format
    """

    articles = []

    try:
        # feedparser.parse() fetches the URL and parses the XML.
        # It's synchronous and handles redirects, encoding, etc automatically.
        feed = feedparser.parse(rss_url)

        if feed.bozo:
            # bozo = True means feedparser encountered a malformed feed.
            # It often still parses successfully, so we warn but continue.
            print(f"[RSS] Warning: malformed feed from {source_name}")
        
        for entry in feed.entries:
            # RSS entries use differnt field names across publishers.
            # We try multiple fallbacks to get the best data available.

            title = entry.get("title", "").strip()
            url = entry.get("link", "")

            # Skip entries without a url - we cant identify them
            if not url:
                continue
            
            # Summary: try 'summary' first, fall back to 'description'
            summary = entry.get("summary", entry.get("description", ""))

            # published_parsed is a time.struct_time from feedparser.
            # It is converted to an ISO 8601 string to match NewsAPI format.
            published_at = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published_at = datetime(
                    *entry.published_parsed[:6]
                ).isoformat() + "Z"
            
            articles.append({
                "title": title,
                "summary": summary,
                "body": "",           # RSS rarely includes full body text
                "url": url,
                "published_at": published_at,
                "source_name": source_name,
            })

    except Exception as e:
        print(f"[RSS] Failed to fetch {source_name} ({rss_url}): {e}")
    
    return articles

def fetch_all_rss_feeds(sources: list[dict]) -> list[dict]:
    """
    Fetches RSS feeds for all sources that have an rss_url.
    
    Args:
        sources: List of source records from the database
    
    Returns:
        Combined list of articles from all feeds
    """
    all_articles = []

    for source in sources:
        if not source.get("rss_url"):
            continue    # Skip sources with no RSS feed
        
        print(f"[RSS] Fetching: {source['name']}")
        articles = fetch_rss_feed(source["name"], source["rss_url"])
        all_articles.extend(articles)

        # Adding a small delay between requests.
        # Hammering servers too fast can get your IP blocked.
        time.sleep(0.5)
    
    print(f"[RSS] Fetched {len(all_articles)} articles total")
    return all_articles