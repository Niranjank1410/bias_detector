# backend/api/routes/categories.py
"""
Category endpoints.

GET /categories  → list all categories with story counts
"""

from fastapi import APIRouter
from backend.db.client import supabase
from backend.api.models import CategorySummary

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("", response_model=list[CategorySummary])
def get_categories():
    """
    Returns all categories that have at least one story cluster,
    with the count of stories in each. Ordered by count descending.
    """
    response = (
        supabase.table("story_clusters")
        .select("category")
        .not_.is_("category", "null")
        .not_.is_("divergence_score", "null")
        .execute()
    )

    # Count occurrences of each category in Python
    # (Supabase free tier doesn't support GROUP BY via the client library)
    counts: dict[str, int] = {}
    for row in response.data:
        cat = row.get("category")
        if cat:
            counts[cat] = counts.get(cat, 0) + 1

    categories = [
        CategorySummary(category=cat, article_count=count)
        for cat, count in counts.items()
    ]

    categories.sort(key=lambda c: c.article_count, reverse=True)
    return categories