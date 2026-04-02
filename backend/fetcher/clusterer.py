# backend/fetcher/clusterer.py

"""
Groups articles about the same event into story clusters.

The algorithm:
1. Generate sentence embeddings for each article's title + summary
2. Compute pairwise cosine similarity between all articles
3. Run DBSCAN to find natural clusters (groups of similar articles)
4. Each cluster represents a single real-world story/event

Why DBSCAN over K-Means?
- K-Means requires you to specify the number of clusters in advance.
  We don't know how many unique stories there are each day.
- DBSCAN discovers clusters automatically based on density.
  It also handles noise (singleton articles that don't cluster with anything).
"""

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import cosine_similarity

# load the model once at module level.
# This downloads ~90MB on first run and caches it locally afterward.
# all-MiniLM-L6-v2 is a great balance of speed and accuracy for english text.

print("[Clusterer] Loading sentence transformer model...")
model = SentenceTransformer("all-MiniLM-L6-v2")
print("[Clusterer] Model loaded.")

def generate_embeddings(articles: list[dict]) -> np.ndarray:
    """
    Converts article text into vector embeddings.
    
    We concatenate title + summary because:
    - Title alone is often too short for good similarity
    - Summary adds context but isn't as critical as the title
    
    Returns:
        numpy array of shape (num_articles, 384)
    """

    texts = []
    for article in articles:
        title = article.get("title", "")
        summary = article.get("summary", "")
        if summary and len(summary) > 30:
            combined = f"{title}. {title}. {summary}".strip()
        else:
            combined = f"{title}. {title}".strip()
        
        texts.append(combined)

    # encode() processes all texts in a batch, which is much faster
    # than encoding one-by-one. show_progress_bar=True helps when debugging.
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=32)
    return embeddings

def cluster_articles(articles: list[dict]) -> list[list[dict]]:
    """
    Groups articles into story clusters using DBSCAN.
    
    Args:
        articles: List of article dicts
    
    Returns:
        List of clusters, where each cluster is a list of article dicts.
        E.g.: [[article1_bbc, article1_guardian], [article2_reuters], ...]
    """

    if len(articles) < 2:
        # Cant cluster with fewer than 2 articles
        return [[a] for a in articles]
    
    print(f"[Clusterer] Generating embeddings for {len(articles)} articles...")
    embeddings = generate_embeddings(articles)

    # Compute cosine similarity matrix.
    # similarity_matrix[i][j] is the similarity between article i and article j.
    # Values range from 0 (completely different) to 1 (identical meaning).
    similarity_matrix = cosine_similarity(embeddings)

    # Convert similarity to distance for DBSCAN.
    # DBSCAN needs distances, not similarities. Distance = 1 - similarity.
    distance_matrix = 1 - similarity_matrix
    # Clip to [0,1] to avoid floating point rounding issues like -0.0000001
    distance_matrix = np.clip(distance_matrix, 0, 1)

     # Run DBSCAN clustering.
    # eps: the maximum distance between two articles to be considered neighbours.
    #      0.25 means articles must be >75% similar to be grouped together.
    #      Tune this if clusters are too tight or too loose.
    # min_samples: minimum articles to form a cluster. 
    #      1 means even single articles form their own cluster (no noise rejection).
    # metric='precomputed': tells DBSCAN we're providing distances directly.
    dbscan = DBSCAN(eps = 0.15, min_samples = 1, metric = "precomputed")
    labels = dbscan.fit_predict(distance_matrix)

    # labels is an array like [0, 0, 1, 2, 0, 1, 3, ...]
    # Articles with the same label belong to the same cluster.
    # Label -1 means noise (not assigned to any cluster) — only happens
    # when min_samples > 1, so we won't see it with our settings.

    # Group articles by their cluster label
    clusters: dict[int, list[dict]] = {}
    for idx, label in enumerate(labels):
        if label not in clusters:
            clusters[label] = []
        clusters[label].append(articles[idx])
        # Also store the embedding with the article for later DB storage
        articles[idx]["_embedding"] = embeddings[idx].tolist()

    cluster_list = list(clusters.values())
    multi_source = sum(1 for c in cluster_list if len(c) > 1)

    print(f"[Clusterer] Found {len(cluster_list)} clusters ({multi_source} with multiple sources)")
    return cluster_list

def pick_canonical_headline(cluster: list[dict]) -> str:
    """
    Chooses the best representative headline for a cluster.
    
    Strategy: pick the longest title (usually the most descriptive).
    In a future version, a summarization model could be used here.
    """

    return max(cluster, key=lambda a: len(a.get("title", "")))["title"]