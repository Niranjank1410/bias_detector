# backend/fetcher/pipeline.py

"""
The main daily pipeline.

This script is what gets run every day (either manually or by a scheduler).
It orchestrates the full flow:
  Fetch → Deduplicate → Cluster → Store
"""

from backend.fetcher.newsapi_fetcher import fetch_top_headlines
from backend.fetcher.rss_fetcher import fetch_all_rss_feeds
from backend.fetcher.deduplicator import deduplicate_articles
from backend.fetcher.clusterer import cluster_articles
from backend.db.writer import get_source_map, insert_articles, save_clusters
from backend.db.client import supabase

def run_pipeline():
    print("=" * 50)
    print("Bias Detector Pipeline - Starting")
    print("=" * 50)

    # Step 1: Get all active sources from the DB
    sources_response = supabase.table("sources").select("*").eq("is_active", True).execute()
    sources = sources_response.data
    source_map = get_source_map()
    print(f"[Pipeline] Loaded {len(sources)} active sources")

    # Step 2: Fetch articles fro all sources
    newsapi_articles = fetch_top_headlines()
    rss_articles = fetch_all_rss_feeds(sources)
    all_articles = newsapi_articles + rss_articles
    print(f"[Pipeline] Total fetched: {len(all_articles)} articles")

    # Step 3: Deduplicate
    unique_articles = deduplicate_articles(all_articles)

    # Step 4: Cluster articles by story
    clusters = cluster_articles(unique_articles)

    # Step 5: Store articles to DB
    insert_articles(unique_articles, source_map)

    # Step 6: Store clusters and links
    save_clusters(clusters, source_map)

    # Step 7: Run ML processing on newly inserted articles
    print("[Pipeline] Starting ML processing stage...")
    from backend.models.ml_pipeline import run_ml_pipeline
    run_ml_pipeline()

    print("=" * 50)
    print(f"[Pipeline] Done. {len(unique_articles)} articles, {len(clusters)} clusters.")
    print("=" * 50)

if __name__ == "__main__":
    run_pipeline()    