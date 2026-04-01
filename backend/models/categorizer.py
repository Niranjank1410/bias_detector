# backend/models/categoriser.py
"""
Categorises news articles into topic areas using zero-shot classification.

Model: facebook/bart-large-mnli
- Zero-shot: no training data needed
- We give it candidate labels and it scores each one
- Downloads ~1.6GB on first run, cached locally afterward

Why zero-shot over a fine-tuned classifier?
- No labelled training data needed
- Easy to add/remove categories by changing the list
- Good enough accuracy for the use case (~85-90% on news)
"""

from transformers import pipeline
from backend.models.device import get_device

# Categories to classify the articles into
CATEGORIES = [
    "Politics",
    "Technology",
    "Business",
    "Health",
    "Science",
    "Environment",
    "Sport",
    "Entertainment",
    "World News",
    "Crime",
]

print("[Categoriser] Loading zero-shot classification model...")
_classifier = pipeline(
    "zero-shot-classification",
    model = "facebook/bart-large-mnli",
    device = 0 if get_device() == "cuda" else -1,
    # device = 0 means first GPU, device = -1 means CPU
)
print("[Categoriser] Model ready.")

# Keyword rules that override the ML model when confidence is low.
# Format: {category: [keywords that strongly indicate this category]}
KEYWORD_OVERRIDES = {
    "Sport": [
        "premier league", "champions league", "fifa", "uefa", "formula 1", "f1",
        "grand prix", "wimbledon", "cricket", "rugby", "nfl", "nba", "transfer",
        "goal", "match", "tournament", "championship", "olympic", "paralympic",
    ],
    "Technology": [
        "artificial intelligence", "ai model", "chatgpt", "openai", "google deepmind",
        "iphone", "android", "cybersecurity", "hack", "data breach", "startup",
        "silicon valley", "semiconductor", "app store", "software update",
    ],
    "Health": [
        "nhs", "hospital", "cancer", "vaccine", "mental health", "pandemic",
        "clinical trial", "medication", "surgery", "disease outbreak", "who ",
    ],
    "Business": [
        "stock market", "ftse", "nasdaq", "interest rate", "inflation", "gdp",
        "central bank", "hedge fund", "ipo", "merger", "acquisition", "earnings",
    ],
    "Environment": [
        "climate change", "global warming", "carbon", "net zero", "renewable",
        "solar", "wind farm", "biodiversity", "deforestation", "plastic pollution",
    ],
}


def keyword_override(title: str, summary: str, ml_category: str, ml_confidence: float) -> str:
    """
    Checks if strong keyword signals should override the ML prediction.
    Only overrides when ML confidence is below 0.6.
    """
    if ml_confidence >= 0.6:
        return ml_category  # Trust the model when it's confident

    text = f"{title} {summary}".lower()

    for category, keywords in KEYWORD_OVERRIDES.items():
        for keyword in keywords:
            if keyword in text:
                return category

    return ml_category

def categorize_article(title: str, summary: str = "") -> dict:
    """
    Classifies an article into one of the predefined categories.

    Args:
        title: Article headline
        summary: Short description (optional but improves accuracy)

    Returns:
        dict with keys:
        - category: the top predicted category (str)
        - scores: dict of all categories and their confidence scores
    """
    # Combine title and summary for better context.
    # Truncate to 512 chars — BART has a token limit and long inputs
    # don't meaningfully improve accuracy for this task.
    text = f"{title}. {summary}"[:512]

    result = _classifier(
        text,
        candidate_labels = CATEGORIES,
        # multi_label = False means we want ONE best category,
        # not multiple simultaneously true labels
        multi_label = False,
    )

    top_category = result["labels"][0]
    top_score = result["scores"][0]
    
    # If confidence is low, fall back to "World News"
    # rather than making a bad guess. 0.35 is a good threshold for
    # bart-large-mnli on news text.

    if top_score < 0.35:
        top_category = "World News"

    # Applying keyword override for low-confidence predictions
    final_category = keyword_override(title, summary, top_category, top_score)
    return {
        "category": final_category,
        "confidence": top_score,
        "scores": dict(zip(result["labels"], result["scores"])),
    }


def categorise_batch(articles: list[dict]) -> list[dict]:
    """
    Categorises a list of articles, adding 'category' to each dict.
    Processes in batch for efficiency.

    Args:
        articles: List of article dicts with 'title' and 'summary' keys

    Returns:
        Same list with 'category' key added to each article
    """
    print(f"[Categoriser] Categorising {len(articles)} articles...")

    texts = [
        f"{a.get('title', '')}. {a.get('summary', '')}"[:512]
        for a in articles
    ]

    # Pipeline accepts a list for batch processing - much faster than
    # calling one-by-one because GPU can process multiple inputs at once
    results = _classifier(
        texts,
        candidte_label = CATEGORIES,
        multi_label = False,
        batch_size = 8      # Process 8 at a time - tune down if there are OOM (Out Of Memory) errors
    )

    for article, result in zip(articles, results):
        article["category"] = result["labels"][0]
        article["category_scores"] = dict(zip(result["labels"], result["scores"]))

    print(f"[Categoriser] Done.")
    return articles