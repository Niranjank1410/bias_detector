"""
Detects whether an article was likely written by an AI.

Model: Hello-SimpleAI/chatgpt-detector-roberta
- Fine-tuned RoBERTa model specifically for detecting ChatGPT-generated text
- Returns a probability score between 0.0 (human) and 1.0 (AI)
- Downloads ~500MB on first run

Important caveat: AI detection is an imperfect science.
- False positives (human text flagged as AI) do occur
- The model was trained on ChatGPT text — other models may fool it
- We surface the score as a probability, not a verdict, so users
  understand the uncertainty
"""

from transformers import pipeline
from backend.models.device import get_device

print ("[AI Detector] Loading model...")
_detector = pipeline(
    "text-classification",
    model = "Hello-SimpleAI/chatgpt-detector-roberta",
    device = 0 if get_device() == "cuda" else -1,
    truncation = True,      # Automatically truncate text that is too long
    max_length = 512,
)
print("[AI Detector] Model ready.")

def detect_ai(text: str) -> dict:
    """
    Scores a piece of text for AI authorship likelihood.

    Args:
        text: The article body or title+summary if body unavailable

    Returns:
        dict with keys:
        - ai_score: float 0.0-1.0 (higher = more likely AI written)
        - label: 'AI' or 'Human'
        - confidence: the model's confidence in its prediction
    """
    if not text or len(text.strip()) <50:
        # Too short to make a meaningful prediction
        return {"ai_score": None, "label": "unknown", "confidence": 0.0}
    
    result = _detector(text[:1024])[0]
    # result looks like: {'label': 'ChatGPT', 'score': 0.94}
    # or:                {'label': 'Human', 'score': 0.87}

    label = result["label"]
    confidence = result["score"]

    # Normalise: if the model says "Human" with 0.87 confidence,
    # the AI score is 1 - 0.87 = 0.13

    if "human" in label.lower():
        ai_score = 1.0 - confidence
        normalised_label = "Human"
    else:
        ai_score = confidence
        normalised_label = "AI"

    return {
        "ai_score": round(ai_score, 4),
        "label": normalised_label,
        "confidence": round(confidence, 4),
    }    

def detect_ai_batch(articles: list[dict]) -> list[dict]:
    """
    Runs AI detection on a list of articles.
    Uses body text if available, falls back to title + summary.

    Args:
        articles: List of article dicts

    Returns:
        Same list with 'ai_score' key added to each article
    """
    print(f"[AI Detector] Processing {len(articles)} articles...")

    for article in articles:
        # Prefer body text — more text = more reliable detection.
        # Fall back to title + summary if body is empty (common with RSS)
        text = article.get("body") or f"{article.get('title', '')} {article.get('summary', '')}"
        result = detect_ai(text)
        article["ai_score"] = result["ai_score"]
        article["ai_label"] = result["label"]

    print(f"[AI Detector] Done.")
    return articles
