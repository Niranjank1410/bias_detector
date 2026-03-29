# backend/fetcher/deduplicator.py
"""
Removes truly identical duplicate articles before DB insertion.

We only remove exact duplicates here (same URL or identical title).
Grouping articles about the same STORY from different sources is the
clusterer's job — not the deduplicator's.
"""

def deduplicate_articles(articles: list[dict]) -> list[dict]:
    # --- Pass 1: Exact URL deduplication ---
    seen_urls = set()
    url_deduped = []

    for article in articles:
        url = article.get("url", "").strip().rstrip("/")
        if url and url not in seen_urls:
            seen_urls.add(url)
            url_deduped.append(article)

    print(f"[Dedup] After URL dedup: {len(url_deduped)} articles (removed {len(articles) - len(url_deduped)})")

    # --- Pass 2: Exact title deduplication ---
    # Only removes articles with the literally identical title string,
    # e.g. if the same article appears in both NewsAPI and RSS feeds.
    seen_titles = set()
    title_deduped = []

    for article in url_deduped:
        title = article.get("title", "").strip().lower()
        if title and title not in seen_titles:
            seen_titles.add(title)
            title_deduped.append(article)

    print(f"[Dedup] After title dedup: {len(title_deduped)} articles (removed {len(url_deduped) - len(title_deduped)})")
    return title_deduped