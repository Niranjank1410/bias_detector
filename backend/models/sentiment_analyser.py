"""
Runs sentiment analysis on article text.

Model: cardiffnlp/twitter-roberta-base-sentiment-latest
- Fine-tuned RoBERTa on ~124M tweets, then adapted for general text
- Returns: Positive / Negative / Neutral with confidence scores
- Downloads ~500MB on first run

This is one of three signals used to detect bias:
- If Source A covers an event with strongly negative sentiment
  and Source B covers the same event with positive sentiment,
  that divergence is a measurable framing difference.

Raw sentiment scores are stored now and the bias divergence
score is computed in a later step once we have all articles in a cluster scored.
"""

from transformers import pipeline
from backend.models.device import get_device

print("[Sentiment] Loading model...")
_sentiment = pipeline(
    "sentiment-analysis",
    model = "cardiffnlp/twitter-roberta-base-sentiment-latest",
    device=0 if get_device() == "cuda" else -1,
    truncation=True,
    max_length=512,
    top_k=None,   # Return scores for ALL labels, not just the top one
)
print("[Sentiment] Model ready.")

# Map model label names to clean names
LABEL_MAP = {
    "positive": "positive",
    "negative": "negative",
    "neutral": "neutral",
}

def analyse_sentiment(text: str) -> dict:
    """
    Analyses the sentiment of a piece of text.

    Args:
        text: Article body, or title + summary

    Returns:
        dict with keys:
        - label: 'positive', 'negative', or 'neutral'
        - score: confidence of the top label (0.0-1.0)
        - scores: dict of all three label scores
    """
    if not text or len(text.strip()) <20:
        return {"label": "neutral", "score": 0.5, "scores":{}}
    
    result = _sentiment(text[:512])[0]
    # result is a list of dicts: [{'label': 'positive', 'score': 0.8}, ...]

    # Sort by score to find top label
    sorted_result = sorted(result, key = lambda x: x["score"], reverse = True)
    top = sorted_result[0]

    label = LABEL_MAP.get(top["label"].lower(), top["label"].lower())
    scores = {
        LABEL_MAP.get(r["label"].lower(), r["label"].lower()): round(r["score"], 4)
        for r in result
    }

    return {
        "label": label,
        "score": round(top["score"], 4),
        "scores": scores,
    }


def analyse_sentiment_batch(articles: list[dict]) -> list[dict]:
    """
    Runs sentiment analysis on a list of articles.

    Args:
        articles: List of article dicts

    Returns:
        Same list with 'sentiment_label' and 'sentiment_score' keys added
    """
    print(f"[Sentiment] Analysing {len(articles)} articles...")

    for article in articles:
        text = article.get("body") or f"{article.get('title', '')} {article.get('summary', '')}"
        result = analyse_sentiment(text)
        article["sentiment_label"] = result["label"]
        article["sentiment_score"] = result["score"]
        article["sentiment_scores"] = result["scores"]

    print(f"[Sentiment] Done.")
    return articles
