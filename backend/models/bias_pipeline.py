"""
Bias analysis pipeline — runs after the ML pipeline.

Order of operations:
1. Lexical framing analysis (needs articles to be ML-processed first)
2. Divergence scoring (needs framing scores from step 1)
3. Source profile update (needs divergence scores from step 2)
"""
# backend/models/bias_pipeline.py  
import os
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"

from backend.models.lexical_framer import run_lexical_framing
from backend.models.divergence_scorer import score_all_clusters
from backend.models.source_profiler import update_all_source_profiles

def run_bias_pipeline():
    print("=" * 50)
    print("Bias Analysis Pipeline - Starting")
    print("=" * 50)

    #Step 1: Lexical Framing - find divergent words per article per cluster
    run_lexical_framing()

    # Step 2: Divergence scoring - combine signals into cluster scores
    score_all_clusters()

    # Step 3: Source profiling - roll up signals into per-source profiles
    update_all_source_profiles()

    print("=" * 50)
    print("Bias Analysis Pipeline - Done")
    print("=" * 50)


if __name__ == "__main__":
    run_bias_pipeline()