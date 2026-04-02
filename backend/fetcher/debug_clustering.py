# backend/fetcher/debug_clustering.py
"""
Debug script to show actual similarity scores between articles.
Run this to find the right eps threshold for clustering.
"""

import numpy as np
from backend.db.client import supabase
from backend.fetcher.clusterer import generate_embeddings
from sklearn.metrics.pairwise import cosine_similarity

# Fetch today's articles
response = supabase.table("articles").select(
    "id, title, summary, source_id, sources(name)"
).limit(50).execute()

articles = response.data
print(f"Loaded {len(articles)} articles\n")

embeddings = generate_embeddings(articles)
similarity_matrix = cosine_similarity(embeddings)

# Find the most similar pairs across DIFFERENT sources
print("Top 20 most similar cross-source article pairs:\n")

pairs = []
for i in range(len(articles)):
    for j in range(i + 1, len(articles)):
        source_i = articles[i].get("sources", {}).get("name", "?")
        source_j = articles[j].get("sources", {}).get("name", "?")
        
        # Only show cross-source pairs
        if source_i != source_j:
            pairs.append((
                similarity_matrix[i][j],
                articles[i]["title"][:60],
                source_i,
                articles[j]["title"][:60],
                source_j,
            ))

pairs.sort(reverse=True)

for score, title_i, source_i, title_j, source_j in pairs[:20]:
    print(f"Similarity: {score:.3f}")
    print(f"  [{source_i}] {title_i}")
    print(f"  [{source_j}] {title_j}")
    print()