# backend/models/lexical_framer.py
"""
Lexical framing analysis — finds words that reveal how differently
sources frame the same story.

How it works:
1. For each story cluster, collect all article texts grouped by source
2. Build a TF-IDF matrix across all texts in the cluster
3. For each source, find words that score high in their text but
   low in other sources' texts — these are "divergent words"
4. Cross-reference against a list of charged/loaded words to flag
   particularly opinionated language choices

Example output for a story about protests:
  BBC News:     ['march', 'demonstration', 'gathered']
  Daily Mail:   ['mob', 'chaos', 'disorder']          ← charged framing
  Guardian:     ['solidarity', 'peaceful', 'rights']  ← charged framing

The difference in word choice IS the bias signal.
"""

import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from backend.db.client import supabase


# Words that carry strong political/emotional charge.
# When a source uses these, it's a strong framing signal.
# This list is deliberately cross-spectrum — charged words exist on all sides.
CHARGED_WORDS = {
    # Conflict framing
    "terrorist", "militant", "freedom fighter", "insurgent", "extremist",
    "radical", "thug", "mob", "rioter", "protester", "activist",
    # Political charge
    "regime", "government", "administration", "junta", "establishment",
    "propaganda", "narrative", "agenda", "scheme", "plot",
    # Evaluative
    "controversial", "divisive", "landmark", "historic", "unprecedented",
    "disastrous", "catastrophic", "successful", "failed", "brilliant",
    "dangerous", "necessary", "illegal", "legitimate", "shocking",
    # People framing
    "leader", "dictator", "strongman", "president", "official",
    "denier", "critic", "supporter", "ally", "opponent",
}

# Common words to exclude — these appear everywhere and carry no signal
STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
    "for", "of", "with", "by", "from", "as", "is", "was", "are",
    "were", "be", "been", "being", "have", "has", "had", "do",
    "does", "did", "will", "would", "could", "should", "may", "might",
    "said", "says", "say", "told", "tell", "according", "also",
    "after", "before", "about", "over", "under", "more", "than",
    "that", "this", "which", "who", "what", "when", "where", "how",
    "not", "no", "its", "it", "he", "she", "they", "we", "his",
    "her", "their", "our", "your", "my",
}

def extract_keywords(text: str, max_words: int = 20) -> list[str]:
    """
    Extracts meaningful keywords from text using basic TF-style scoring.
    Removes stopwords and short tokens.
    """
    # Lowercase and split on non_alphabetic characters
    words = re.findall(r"[a-z]{3,}", text.lower())
    # Remove stopwords
    words = [w for w in words if w not in STOPWORDS]
    # Count frequency
    freq = {}
    for word in words:
        freq[words] = freq.get(word, 0) + 1
    # Sort by frequency, return top N
    sorted_words = sorted(freq.items(), key = lambda x: x[1], reverse = True)
    return [w for w, _ in sorted_words[:max_words]]

def find_charged_words(text: str) -> list[str]:
    """Finds charged/loaded words present in a text"""
    text_lower = text.lower()
    found = []
    for word in CHARGED_WORDS:
        if word in text_lower:
            found.append(word)
    return found

def analyse_cluster_framing(cluster_id: str) -> list[dict]:
    """
    Analyses lexical framing for all articles in a cluster.
    
    For each article:
    - Finds words that are prominent in this source but not others
    - Identifies any charged/loaded language
    - Computes a framing score (how different is this source's language?)
    
    Args:
        cluster_id: UUID of the story cluster
    
    Returns:
        List of framing result dicts, one per article
    """

    # Fetch all articles in this cluster with their source info
    response = (
        supabase.table("cluster_articles")
        .select("article_id, articles(id, title, summary, body, source_id)")
        .eq("cluster_id", cluster_id)
        .execute()
    )

    articles = [row["articles"] for row in response.data if row.get("articles")]

    if len(articles) < 2:
        # Framing analysis needs at least 2 sources to compare
        return[]
    
    # Build texts for TF-IDF - one "document" per article
    texts = []
    for article in articles:
        text = article.get("body") or f"{article.get('title', '')} {article.get('summary', '')}"
        texts.append(text)

    # TF-IDF vectoriser:
    # TF = Term Frequency (how often a word appears in THIS document)
    # IDF = Inverse Document Frequency (how rare is this word across ALL documents)
    # TF-IDF score is high for words that are frequent in one document
    # but rare across others — exactly what we want for divergence detection
    try:
        vectorizer = TfidfVectorizer(
            max_features=200,
            stop_words="english",
            ngram_range=(1, 2),      # Include both single words and 2-word phrases
            min_df=1,
            sublinear_tf=True,      # Apply log scaling to term frequencies
        )
        tfidf_matrix = vectorizer.fit_transform(texts)
        feature_names = vectorizer.get_feature_names_out()
    except ValueError:
        # Can happen if texts are too short or all identical
        return[]
    
    results = []
    tfidf_array = tfidf_matrix.toarray()

    for i, article in enumerate(articles):
        source_scores = tfidf_array[i]

        # Compute average scores for all OTHER sources
        other_scores = np.mean(
            [tfidf_array[j] for j in range(len(articles)) if j != i],
            axis=0 
        )

        # Divergent words: high score in THIS source, low in others
        # We measure this as (this_score - avg_other_score)
        divergence = source_scores - other_scores
        top_divergent_indices = np.argsort(divergence)[-10:][::-1]
        divergent_words = [
            feature_names[idx]
            for idx in top_divergent_indices
            if divergence[idx] > 0.05
        ]

        # Charged words present in this article
        full_text = article.get("body") or f"{article.get('title', '')} {article.get('summary', '')}"
        charged = find_charged_words(full_text)

        # Framing score: average divergence of top words, scaled to 0-100
        framing_score = float(np.mean(divergence[top_divergent_indices])) * 100
        framing_score = round(min(max(framing_score, 0), 100), 2)

        results.append({
            "cluster_id": cluster_id,
            "article_id": article["id"],
            "source_id": article["source_id"],
            "divergent_words": divergent_words[:10],
            "charged_words": charged[:10],
            "framing_score": framing_score,
        })

    return results

def run_lexical_framing():
    """
    Runs lexical framing analysis on all clusters that have
    multiple sources and haven't been framed yet.
    """
    print("[Lexical] Running framing analysis...")

    # Get clusters with 2+ sources
    clusters_response = (
        supabase.table("story_clusters")
        .select("id")
        .gte("source_count", 2)
        .execute()
    )

    clusters = clusters_response.data
    print(f"[Lexical] Analysing {len(clusters)} multi-source clusters...")

    saved = 0
    for cluster in clusters:
        cluster_id = cluster["id"]
        results = analyse_cluster_framing(cluster_id)

        for result in results:
            try:
                # Save to lexical_frames
                supabase.table("lexical_frames").upsert({
                    "cluster_id": result["cluster_id"],
                    "article_id": result["article_id"],
                    "source_id": result["source_id"],
                    "charged_words": result["charged_words"],
                    "divergent_words": result["divergent_words"],
                    "framing_score": result["framing_score"],
                }, on_conflict="cluster_id,article_id", ignore_duplicates=False).execute()

                # Also update the framing_score in bias_reports
                supabase.table("bias_reports").update({
                    "framing_score": result["framing_score"],
                }).eq("article_id", result["article_id"]).eq("cluster_id", result["cluster_id"]).execute()

                saved += 1
            except Exception as e:
                print(f"[Lexical] Failed to save framing result: {e}")
    print(f"[Lexical] Saved {saved} framing results.")
    