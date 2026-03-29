# backend/models/ml_pipeline.py
"""
ML processing pipeline — runs after the fetch pipeline.

Fetches all articles where ml_processed = FALSE, runs the three
models on each, and writes results back to the database.

We separate this from the fetch pipeline so that:
1. If the ML step crashes, fetched articles are still safely stored
2. We can re-run ML processing independently without re-fetching
3. In production we can run fetch more frequently than ML processing
"""

from backend.db.client import supabase
from backend.db.writer import (
    update_article_ml_fields,
    save_sentiment_reports,
)

# Import models — this triggers model loading, so expect a delay
# the first time this runs while models download
from backend.models.categorizer import categorize_article
from backend.models.ai_detector import detect_ai
from backend.models.sentiment_analyser import analyse_sentiment


def fetch_unprocessed_articles() -> list[dict]:
    """
    Fetches all articles that haven't been through ML processing yet.
    Joins with cluster_articles and sources to get the IDs we need.
    """
    response = (
        supabase.table("articles")
        .select("id, title, summary, body, source_id, cluster_articles(cluster_id)")
        .eq("ml_processed", False)
        .limit(100)   # Process in batches of 100 to avoid memory issues
        .execute()
    )
    return response.data


def run_ml_pipeline():
    print("=" * 50)
    print("ML Processing Pipeline — Starting")
    print("=" * 50)

    articles = fetch_unprocessed_articles()

    if not articles:
        print("[ML Pipeline] No unprocessed articles found. Exiting.")
        return

    print(f"[ML Pipeline] Processing {len(articles)} articles...")

    for i, article in enumerate(articles):
        article_id = article["id"]
        source_id = article["source_id"]
        title = article.get("title", "")
        summary = article.get("summary", "")
        body = article.get("body", "")

        # Use body if available, fall back to title + summary
        text = body if body and len(body) > 100 else f"{title}. {summary}"

        print(f"[ML Pipeline] ({i+1}/{len(articles)}) {title[:60]}...")

        # --- Run the three models ---
        cat_result = categorize_article(title, summary)
        ai_result = detect_ai(text)
        sentiment_result = analyse_sentiment(text)

        # --- Write ML fields back to the articles table ---
        update_article_ml_fields(
            article_id=article_id,
            category=cat_result["category"],
            ai_score=ai_result["ai_score"],
        )

        # --- Write sentiment to bias_reports for each cluster ---
        # An article could theoretically be in multiple clusters,
        # so we loop over all cluster links
        cluster_links = article.get("cluster_articles", [])
        for link in cluster_links:
            cluster_id = link.get("cluster_id")
            if cluster_id:
                save_sentiment_reports(
                    cluster_id=cluster_id,
                    article_id=article_id,
                    source_id=source_id,
                    sentiment={
                        "sentiment_label": sentiment_result["label"],
                        "sentiment_score": sentiment_result["score"],
                    },
                )

    print("=" * 50)
    print(f"[ML Pipeline] Done. Processed {len(articles)} articles.")
    print("=" * 50)


if __name__ == "__main__":
    run_ml_pipeline()