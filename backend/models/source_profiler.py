# backend/models/source_profiler.py
"""
Builds and updates per-source bias profiles.

A source profile aggregates all of a source's bias signals into
a single summary that updates with each pipeline run.

This answers questions like:
- "Does the Guardian consistently use more negative sentiment
   than the Telegraph when covering the same stories?"
- "Which sources consistently use the most charged language?"
- "Which sources get the highest divergence scores?"

These profiles power the "Source Analysis" page on the frontend.
"""

import numpy as np
from backend.db.client import supabase

def build_source_profile(source_id: str) -> dict:
    """
    Computes a fresh bias profile for a single source.
    
    Aggregates all bias_reports and lexical_frames for this source
    into summary statistics.
    
    Args:
        source_id: UUID of the source
    
    Returns:
        Profile dict ready for upsert into source_profiles
    """

    # Fetch all bias reports for this source
    reports_response =(
        supabase.table("bias_reports")
        .select("sentiment_label, sentiment_score, framing_score, bias_score")
        .eq("source_id", source_id)
        .execute()
    )
    reports = reports_response.data

    if not reports:
        return None
    
    # Compute sentiment distribution
    labels = [r["sentiment_label"] for r in reports if r.get("sentiment_label")]
    total = len(labels)

    positive_pct = round(labels.count("positive") / total * 100, 1) if total else 0
    negative_pct = round(labels.count("negative") / total * 100, 1) if total else 0
    neutral_pct = round(labels.count("neutral") / total * 100, 1) if total else 0

    # A verage sentiment score (0-1)
    scores = [r["sentiment_score"] for r in reports if r.get("sentiment_score") is not None]
    avg_sentiment = round(float(np.mean(scores)), 4) if scores else 0.5

    # Average framing score (0-100)
    framing_scores = [r["framing_score"] for r in reports if r.get("framing_score") is not None]
    avg_framing = round(float(np.mean(framing_scores)), 2) if framing_scores else 0.0

    # Average bias score (0-100) — will be 0 until divergence scorer runs
    bias_scores = [r["bias_score"] for r in reports if r.get("bias_score") is not None]
    avg_bias = round(float(np.mean(bias_scores)), 2) if bias_scores else 0.0

    # Top divergent words across all this source's articles
    lexical_response = (
        supabase.table("lexical_frames")
        .select("divergent_words, charged_words")
        .eq("source_id", source_id)
        .limit(50)
        .execute()
    )

    # Flatten and count all divergent words across articles
    all_divergent = []
    for row in lexical_response.data:
        all_divergent.extend(row.get("divergent_words") or [])
        all_divergent.extend(row.get("charged_words") or [])
    
    # Get the most frequently divergent words
    word_freq = {}
    for word in all_divergent:
        word_freq[word] = word_freq.get(word, 0) + 1
    
    top_words = sorted(word_freq.items(), key = lambda x: x[1], reverse = True)
    top_divergent_words = [w for w, _ in top_words[:15]]

    return {
        "source_id": source_id,
        "avg_sentiment_score": avg_sentiment,
        "avg_bias_score": avg_bias,
        "total_articles_analysed": total,
        "positive_pct": positive_pct,
        "negative_pct": negative_pct,
        "neutral_pct": neutral_pct,
        "top_divergent_words": top_divergent_words,
    }

def update_all_source_profiles():
    """
    Rebuilds profiles for all active sources.
    Called at the end of each pipeline run.
    """
    print("[Profiler] Updating source profiles...")

    sources_response = (
        supabase.table("sources")
        .select("id, name")
        .eq("is_active", True)
        .execute()
    )

    updated = 0
    for source in sources_response.data:
        source_id = source["id"]
        profile = build_source_profile(source_id)

        if not profile:
            print(f"[Profiler] No data yet for {source['name']}, skipping.")
            continue

        try:
            supabase.table("source_profiles").upsert(
                {**profile, "last_updated": "now()"},
                on_conflict = "source_id",
            ).execute()
            updated += 1
            print(f"[Profiler] Updated: {source['name']} — {profile['total_articles_analysed']} articles, avg bias: {profile['avg_bias_score']}")
        except Exception as e:
            print(f"[Profiler] Failed to update {source['name']}: {e}")

    print(f"[Profiler] Done. Updated {updated} source profiles.")        

