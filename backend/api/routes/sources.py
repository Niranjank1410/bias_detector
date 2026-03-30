# backend/api/routes/sources.py
"""
Source endpoints.

GET /sources          → list all sources with their bias profiles
GET /sources/{id}     → full profile for one source
"""

from fastapi import APIRouter, HTTPException
from backend.db.client import supabase
from backend.api.models import SourceProfile

router = APIRouter(prefix="/sources", tags=["Sources"])


@router.get("", response_model=list[SourceProfile])
def get_sources():
    """
    Returns all active sources with their rolling bias profiles.
    Ordered by average bias score descending.
    """
    response = (
        supabase.table("sources")
        .select("""
            id, name, url, country, known_lean,
            source_profiles(
                avg_sentiment_score,
                avg_bias_score,
                total_articles_analysed,
                positive_pct,
                negative_pct,
                neutral_pct,
                top_divergent_words
            )
        """)
        .eq("is_active", True)
        .execute()
    )

    sources = []
    for row in response.data:
        profile = row.pop("source_profiles", None)

        # source_profiles is a list (1-to-1 join returns a list in Supabase)
        if isinstance(profile, list):
            profile = profile[0] if profile else None

        sources.append(SourceProfile(
            **row,
            **(profile or {}),
        ))

    # Sort by avg_bias_score descending
    sources.sort(key=lambda s: s.avg_bias_score or 0, reverse=True)
    return sources


@router.get("/{source_id}", response_model=SourceProfile)
def get_source(source_id: str):
    """Returns full profile for a single source."""
    response = (
        supabase.table("sources")
        .select("""
            id, name, url, country, known_lean,
            source_profiles(
                avg_sentiment_score,
                avg_bias_score,
                total_articles_analysed,
                positive_pct,
                negative_pct,
                neutral_pct,
                top_divergent_words
            )
        """)
        .eq("id", source_id)
        .eq("is_active", True)
        .maybe_single()
        .execute()
    )

    if not response.data:
        raise HTTPException(status_code=404, detail="Source not found")

    row = response.data
    profile = row.pop("source_profiles", None)
    if isinstance(profile, list):
        profile = profile[0] if profile else None

    return SourceProfile(**row, **(profile or {}))