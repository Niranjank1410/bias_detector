# backend/db/writer.py
"""
Handles all database write operations.

Responsibilities:
- Look up source IDs by name
- Insert articles (skipping duplicates via the UNIQUE constraint on URL)
- Create story clusters and link articles to them
"""

from datetime import datetime, date
from backend.db.client import supabase

SOURCE_NAME_ALIASES = {
    "Al Jazeera English": "Al Jazeera English",  # already fixed in DB, kept for reference
    "BBC News - Home": "BBC News",
    "Reuters | Breaking International News": "Reuters",
    "The Guardian": "The Guardian",
}

def normalise_source_name(name:str) -> str:
    """Resolves known RSS feed name variants to our canonical DB name."""
    return SOURCE_NAME_ALIASES.get(name, name)

def get_source_map() -> dict[str, str]:
    """
    Fetches all sources from the DB and returns a name → id mapping.
    
    E.g.: {"BBC News": "uuid-1", "Reuters": "uuid-2", ...}
    This avoids doing a DB lookup for every single article.
    """
    response = supabase.table("sources").select("id, name").execute()
    return {row["name"]: row["id"] for row in response.data}

def insert_articles(articles: list[dict], source_map: dict[str, str]) -> list[str]:
    """
    Inserts articles into the database, skipping any that already exist.
    
    The 'url' column has a UNIQUE constraint, so inserting a duplicate URL
    would normally throw an error. on_conflict="ignore" is used to silently
    skip duplicates instead of failing.
    
    Returns:
        List of inserted article IDs (not including skipped duplicates)
    """
    inserted_ids = []

    for article in articles:
        source_name = article.get("source_name", "")
        source_id = source_map.get(normalise_source_name(source_name))

        if not source_id:
            # The article's source isnt in the DB yet.
            # It is skipped for now - later auto-creation of sources can be added.
            print(f"[DB] Unknown source '{source_name}', skipping article: {article['title'][:50]}")
            continue

        # Build the row to insert
        row = {
            "source_id": source_id,
            "title": article.get("title", ""),
            "summary": article.get("summary", ""),
            "body": article.get("body", ""),
            "url": article.get("url", ""),
            "published_at": article.get("published_at")
        }

        try:
            # upsert with on_conflict="ignore" means:
            # "insert this row, but if url already exists, do nothing"
            response = (
                supabase.table("articles")
                .upsert(row, on_conflict="url", ignore_duplicates=True)
                .execute()
            )
            if response.data:
                inserted_ids.append(response.data[0]["id"])
        except Exception as e:
            print(f"[DB] Failed to insert article '{article['title'][:50]}': {e}")

    print(f"[DB] Inserted {len(inserted_ids)} new articles")
    return inserted_ids

def save_clusters(clusters: list[list[dict]], source_map: dict[str, str]):
    """
    Saves story clusters and their article links to the database.
    
    For each cluster:
    1. Create a story_clusters row with the canonical headline
    2. For each article in the cluster, find its DB ID and create
       a cluster_articles row linking them together
    """

    from backend.fetcher.clusterer import pick_canonical_headline

    for cluster in clusters:
        if not cluster:
            continue

        # Skip clusters that are unrealistically large.
        # A real story cluster from 5 sources should never have 74 articles.
        # Large clusters indicate the embeddings are too similar (generic content).
        if len(cluster) > 20:
            print(f"[DB] Skipping oversized cluster ({len(cluster)} articles) — likely generic content")
            continue

        canonical = pick_canonical_headline(cluster)
        today = date.today().isoformat()

        try:
            # Create the cluster record
            cluster_response = (
                supabase.table("story_clusters")
                .insert({
                    "canonical_headline": canonical,
                    "event_date": today,
                })
                .execute()
            )
            cluster_id = cluster_response.data[0]["id"]

            # For each article in this cluster, look up its DB id by URL
            # and create the cluster_articles link

            for article in cluster:
                url = article.get("url", "")
                article_response = (
                    supabase.table("articles")
                    .select("id")
                    .eq("url", url)
                    .maybe_single()
                    .execute()
                )

                if article_response and article_response.data:
                    article_id = article_response.data["id"]
                    supabase.table("cluster_articles").upsert({
                        "cluster_id": cluster_id,
                        "article_id": article_id,
                    }, on_conflict="cluster_id, article_id", ignore_duplicates=True).execute()
                else:
                    print(f"[DB] Article not found in DB, skipping cluster link for: {url[:60]}")

        except Exception as e:
            print(f"[DB] Failed to save cluster '{canonical[:50]}': {e}")
    
    print(f"[DB] Saved {len(clusters)} clusters")

def update_article_ml_fields(article_id: str, category: str, ai_score: float):
    """
    Updates an article's ML-generated fields after processing.

    We do this as a separate UPDATE rather than including it in the
    initial INSERT because the ML models run after the fetch pipeline.
    """
    try:
        supabase.table("articles").update({
            "category": category,
            "ai_score": ai_score,
            "ml_processed": True,
        }).eq("id", article_id).execute()
    except Exception as e:
        print(f"[DB] Failed to update ML fields for article {article_id}: {e}")


def save_sentiment_reports(cluster_id: str, article_id: str, source_id: str, sentiment: dict):
    """
    Saves a sentiment analysis result to the bias_reports table.

    Args:
        cluster_id: The story cluster this article belongs to
        article_id: The article being reported on
        source_id: The source that published this article
        sentiment: Dict with label, score keys from the sentiment analyser
    """
    try:
        supabase.table("bias_reports").upsert({
            "cluster_id": cluster_id,
            "article_id": article_id,
            "source_id": source_id,
            "sentiment_label": sentiment.get("sentiment_label"),
            "sentiment_score": sentiment.get("sentiment_score"),
        }, on_conflict="cluster_id,article_id", ignore_duplicates=True).execute()
    except Exception as e:
        print(f"[DB] Failed to save sentiment report: {e}")

def update_cluster_categories():
    """
    Propagates article categories up to their parent story clusters.
    
    For each cluster, finds the most common category among its articles
    and sets that as the cluster's category. This runs after ML processing
    so categories are available for filtering on the frontend.
    """
    print("[DB] Updating cluster categories...")

    # Fetch all clusters that have no category yet
    clusters_response = (
        supabase.table("story_clusters")
        .select("id")
        .is_("category", "null")
        .execute()
    )

    updated = 0
    for cluster in clusters_response.data:
        cluster_id = cluster["id"]

        # Get all articles in this cluster with their categories
        articles_response = (
            supabase.table("cluster_articles")
            .select("articles(category)")
            .eq("cluster_id", cluster_id)
            .execute()
        )

        # Find the most common category
        categories = [
            row["articles"]["category"]
            for row in articles_response.data
            if row.get("articles") and row["articles"].get("category")
        ]

        if not categories:
            continue

        # Pick the most frequent category
        most_common = max(set(categories), key=categories.count)

        supabase.table("story_clusters").update({
            "category": most_common
        }).eq("id", cluster_id).execute()

        updated += 1

    print(f"[DB] Updated categories for {updated} clusters.")