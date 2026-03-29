# backend/fetcher/deduplicator.py
"""
Removes duplicate articles from a batch before database insertion.

Two types of duplicates to handle:
1. Same URL appearing twice (exact duplicate — easy)
2. Same story with slightly different URLs or titles (fuzzy duplicate — harder)

We use rapidfuzz for fast fuzzy string matching on titles.
"""

from rapidfuzz import fuzz

def deduplicate_articles(articles: list[dict]) -> list[dict]:
    """
    Removes duplicate articles from a list.
    
    Strategy:
    - First, deduplicate by exact URL match (fast O(n) with a set)
    - Then, deduplicate by title similarity using fuzzy matching
    
    Args:
        articles: Raw list of article dicts, possibly containing duplicates
    
    Returns:
        Deduplicated list of article dicts
    """

    # --- Pass 1: Exact URL deduplication ---
    # A Python set only stores unique values, and URL lookup is 0(1)
    seen_urls = set()
    url_deduped = []

    for article in articles:
        url = article.get("url", "").strip().rstrip("/")    # normalise trailing slash
        if url and url not in seen_urls:
            seen_urls.add(url)
            url_deduped.append(article)

    print(f"[Dedup] After URL dedup: {len(url_deduped)} articles (removed {len(articles) - len(url_deduped)})")

    # --- Pass 2: Fuzzy title deduplication ---
    # For each article, compare its title against all already-accepted titles.
    # If similarity >= threshold, it's considered a duplicate.
    #
    # fuzz.token_sort_ratio() is word-order independent:
    # "Biden signs climate bill" and "Climate bill signed by Biden"
    # would score very high, correctly flagging them as the same story.

    SIMILARITY_THRESHOLD = 92   # 0-100, higher = stricter matching

    unique_articles = []
    accepted_titles = []

    for articles in url_deduped:
        title = article.get("title", "")
        is_duplicate = False

        for accepted_title in accepted_titles:
            # token_sort ratio alone is too loose - "Trump signs bill" and
            # "Biden signs bill" score high just because they share common words.
            # Thus 2 metrics are combined: token_sort_ratio(word overlap) and 
            # ratio(character level exact similarity). Both must be high
            # to call something a duplicate.

            sort_score = fuzz.token_sort_ratio(title, accepted_title)
            exact_score = fuzz.ratio(title, accepted_title)

            # Not fuzzy-matching very short titles as it gives too many false positives
            if len(title) < 15:
                unique_articles.append(article)
                accepted_titles.append(title)

            # Only flag as duplicate if both scores are high
            if sort_score >= SIMILARITY_THRESHOLD and exact_score>= 80:
                is_duplicate = True
                break   # No need to check once a match is found
        
        if not is_duplicate:
            unique_articles.append(article)
            accepted_titles.append(title)
    
    print(f"[Dedup] After title dedup: {len(unique_articles)} articles (removed {len(url_deduped) - len(unique_articles)})")
    return unique_articles