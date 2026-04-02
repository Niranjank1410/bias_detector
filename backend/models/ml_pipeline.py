# backend/models/ml_pipeline.py
import os
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"

from backend.db.client import supabase
from backend.db.writer import update_article_ml_fields, save_sentiment_reports
from backend.models.categorizer import categorise_batch
from backend.models.ai_detector import detect_ai_batch
from backend.models.sentiment_analyser import analyse_sentiment_batch


def fetch_unprocessed_articles() -> list[dict]:
    response = (
        supabase.table("articles")
        .select("id, title, summary, body, source_id, cluster_articles(cluster_id)")
        .eq("ml_processed", False)
        .limit(500)
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

    print(f"[ML Pipeline] Processing {len(articles)} articles in batch mode...")

    # --- Step 1: Categorisation (batch) ---
    print("[ML Pipeline] Running categorisation...")
    articles = categorise_batch(articles)

    # --- Step 2: AI Detection (batch) ---
    print("[ML Pipeline] Running AI detection...")
    articles = detect_ai_batch(articles)

    # --- Step 3: Sentiment Analysis (batch) ---
    print("[ML Pipeline] Running sentiment analysis...")
    articles = analyse_sentiment_batch(articles)

    # --- Step 4: Write all results to DB ---
    print("[ML Pipeline] Writing results to database...")
    for article in articles:
        article_id = article["id"]
        source_id = article["source_id"]

        update_article_ml_fields(
            article_id=article_id,
            category=article.get("category"),
            ai_score=article.get("ai_score"),
        )

        cluster_links = article.get("cluster_articles", [])
        for link in cluster_links:
            cluster_id = link.get("cluster_id")
            if cluster_id:
                save_sentiment_reports(
                    cluster_id=cluster_id,
                    article_id=article_id,
                    source_id=source_id,
                    sentiment={
                        "sentiment_label": article.get("sentiment_label"),
                        "sentiment_score": article.get("sentiment_score"),
                    },
                )

    print("=" * 50)
    print(f"[ML Pipeline] Done. Processed {len(articles)} articles.")
    print("=" * 50)


if __name__ == "__main__":
    run_ml_pipeline()