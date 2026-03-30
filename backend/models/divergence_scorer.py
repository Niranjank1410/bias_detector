# backend/models/divergence_scorer.py
"""
Computes bias divergence scores for story clusters.

A divergence score measures how differently sources covered the same event.
Score of 0 = all sources covered it identically.
Score of 100 = maximum disagreement between sources.

Three components feed into the final score:

1. Sentiment Divergence (40% weight)
   Standard deviation of sentiment scores across sources in a cluster.
   High std dev = sources felt very differently about the same story.

2. Framing Score (40% weight)
   How different were the specific words each source chose?
   Computed by the lexical framer and stored in lexical_frames.

3. Coverage Asymmetry (20% weight)
   Did some sources cover this story while others ignored it?
   A story covered by 8/10 sources but ignored by 2 is suspicious.
"""

import numpy as np
from backend.db.client import supabase

def compute_sentiment_divergence(sentiment_scores: list [float]) -> float:
    """
    Computes how spread out the sentiment scores are across sources.
    
    Uses standard deviation — a measure of how much values vary from
    the mean. If all sources scored 0.5 (neutral), std dev = 0.
    If some scored 0.1 (very negative) and others 0.9 (very positive),
    std dev is high.
    
    We normalise to 0-100 by multiplying by 200 (max possible std dev
    for values in [0,1] is 0.5, so 0.5 * 200 = 100).
    
    Args:
        sentiment_scores: List of sentiment scores (0.0-1.0) per source
    
    Returns:
        Divergence score 0-100
    """
    if len(sentiment_scores) < 2:
        # Cant measure divergence with only one source
        return 0.0
    
    std_dev = np.std(sentiment_scores)
    # Normalize to 0-100 scale
    score = min(std_dev * 200, 100)
    return round(float(score), 2)

def compute_coverage_asymmetry(
        sources_that_covered: int,
        total_active_sources: int,
) -> float:
    """
    Scores how asymmetric the coverage was across sources.
    
    If all sources covered a story: asymmetry = 0 (no bias signal)
    If only 1 source covered a story: asymmetry = 100 (strong signal)
    
    The logic: a story ignored by most sources but covered heavily
    by one outlet suggests that outlet has a specific agenda around
    that topic.
    
    Args:
        sources_that_covered: Number of sources that published this story
        total_active_sources: Total number of sources we track
    
    Returns:
        Asymmetry score 0-100
    """
    if total_active_sources == 0:
        return 0.0
    
    coverage_ratio = sources_that_covered / total_active_sources
    # Invert : low coverage ratio = high asymmetry score
    asymmetry = (1 - coverage_ratio) * 100
    return round(asymmetry, 2)

def compute_cluster_divergence_score(
        sentiment_divergence: float,
        avg_framing_score: float,
        coverage_asymmetry: float,
) -> float:
    """
    Combines the three signals into a single divergence score.
    
    Weights:
    - Sentiment divergence: 40% (how differently sources felt about the story)
    - Framing score: 40% (how differently sources worded the story)
    - Coverage asymmetry: 20% (how unevenly the story was covered)
    
    Returns:
        Final divergence score 0-100
    """
    score = (
        (sentiment_divergence * 0.40) +
        (avg_framing_score * 0.40) +
        (coverage_asymmetry * 0.20)
    )
    return round(max(0.0, min(score, 100)), 2)

def score_all_clusters():
    print("[Divergence] Scoring all clusters...")

    clusters_response = (
        supabase.table("story_clusters")
        .select("id, source_count, bias_reports(sentiment_score, sentiment_label, source_id, framing_score)")
        .execute()
    )

    # Get total active sources
    sources_resp = supabase.table("sources").select("id").eq("is_active", True).execute()
    total_active_sources = len(sources_resp.data)
    print(f"[Divergence] Total active sources: {total_active_sources}")

    updated = 0
    for cluster in clusters_response.data:
        cluster_id = cluster["id"]
        reports = cluster.get("bias_reports", [])

        if not reports:
            continue

        sentiment_scores = []
        framing_scores = []

        for report in reports:
            label = report.get("sentiment_label", "neutral")
            score = report.get("sentiment_score", 0.5)
            framing = report.get("framing_score")

            if label == "positive":
                sentiment_scores.append(0.5 + (score * 0.5))
            elif label == "negative":
                sentiment_scores.append(0.5 - (score * 0.5))
            else:
                sentiment_scores.append(0.5)

            if framing is not None:
                framing_scores.append(framing)

        sources_that_covered = len(set(r["source_id"] for r in reports))

        sentiment_divergence = compute_sentiment_divergence(sentiment_scores)
        avg_framing = float(np.mean(framing_scores)) if framing_scores else 0.0
        coverage_asymmetry = compute_coverage_asymmetry(sources_that_covered, total_active_sources)

        # Clamp ALL inputs to valid range before combining
        sentiment_divergence = max(0.0, min(100.0, sentiment_divergence))
        avg_framing = max(0.0, min(100.0, avg_framing))
        coverage_asymmetry = max(0.0, min(100.0, coverage_asymmetry))

        final_score = compute_cluster_divergence_score(
            sentiment_divergence, avg_framing, coverage_asymmetry
        )

        # Debug: print first 3 clusters so we can verify the values
        if updated < 3:
            print(f"[Divergence DEBUG] cluster={cluster_id[:8]}")
            print(f"  sentiment_scores={sentiment_scores[:3]}")
            print(f"  framing_scores={framing_scores[:3]}")
            print(f"  sentiment_divergence={sentiment_divergence}")
            print(f"  avg_framing={avg_framing}")
            print(f"  coverage_asymmetry={coverage_asymmetry}")
            print(f"  final_score={final_score}")

        supabase.table("story_clusters").update({
            "divergence_score": final_score,
            "source_count": sources_that_covered,
        }).eq("id", cluster_id).execute()

        for report in reports:
            supabase.table("bias_reports").update({
                "bias_score": final_score,
            }).eq("cluster_id", cluster_id).eq("source_id", report["source_id"]).execute()

        updated += 1

    print(f"[Divergence] Scored {updated} clusters.")