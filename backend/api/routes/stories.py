# backend/api/routes/stories.py
"""
Story cluster endpoints.

GET /stories         → paginated list of story clusters
GET /stories/{id}    → full detail for one story cluster
"""

from fastapi import APIRouter, HTTPException, Query
from backend.db.client import supabase
from backend.api.models import (
    PaginatedStories,
    StoryClusterSummary,
    StoryClusterDetail,
    ArticleResponse,
    BiasReportResponse,
    SourceSummary,
)

router = APIRouter(prefix = "/stories", tags =["Stories"])

@router.get("", response_model=PaginatedStories)
def get_stories(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Results per page"),
    category: str = Query(default=None, description="Filter by category"),
    min_sources: int = Query(default=1, ge=1, description="Minimum number of sources"),
):
    """
    Returns a paginated list of story clusters.

    Supports filtering by category and minimum source count.
    Ordered by divergence score descending (most contested stories first).
    """
    # Build base query
    query = (
        supabase.table("story_clusters")
        .select("id, canonical_headline, event_date, category, divergence_score, source_count", count="exact")
        .not_.is_("divergence_score", "null")
        .gte("source_count", min_sources)
        .order("divergence_score", desc=True)
    )

    # Apply optional category filter
    if category:
        query = query.eq("category", category)

    # Apply pagination.
    # Supabase uses range() for pagination: range(start, end) is inclusive.
    # Page 1: range(0, 19) = rows 0-19 = 20 results
    # Page 2: range(20, 39) = rows 20-39 = 20 results
    start = (page - 1) * page_size
    end = start + page_size - 1
    response = query.range(start, end).execute()

    stories = [StoryClusterSummary(**row) for row in response.data]

    return PaginatedStories(
        total=response.count or 0,
        page=page,
        page_size=page_size,
        stories=stories,
    )

@router.get("/{story_id}", response_model=StoryClusterDetail)
def get_story_detail(story_id: str):
    """
    Returns full detail for a single story cluster.

    Includes all articles from all sources, with their sentiment
    scores, framing analysis, and divergent word choices.
    """
    # Fetch the cluster itself
    cluster_response = (
        supabase.table("story_clusters")
        .select("*")
        .eq("id", story_id)
        .maybe_single()
        .execute()
    )

    if not cluster_response.data:
        raise HTTPException(status_code=404, detail="Story not found")

    cluster = cluster_response.data

    # Fetch all articles in this cluster via the join table
    articles_response = (
        supabase.table("cluster_articles")
        .select("articles(id, title, summary, url, published_at, category, ai_score, sources(id, name, country, known_lean))")
        .eq("cluster_id", story_id)
        .execute()
    )

    articles = []
    for row in articles_response.data:
        article_data = row.get("articles")
        if not article_data:
            continue

        source_data = article_data.pop("sources", None)
        source = SourceSummary(**source_data) if source_data else None

        articles.append(ArticleResponse(**article_data, source=source))

    # Fetch bias reports for this cluster
    bias_response = (
        supabase.table("bias_reports")
        .select("article_id, sentiment_label, sentiment_score, framing_score, sources(id, name, country, known_lean)")
        .eq("cluster_id", story_id)
        .execute()
    )

    # Fetch lexical frames for enriching bias reports
    lexical_response = (
        supabase.table("lexical_frames")
        .select("article_id, divergent_words, charged_words")
        .eq("cluster_id", story_id)
        .execute()
    )

    # Build a lookup dict for lexical data by article_id
    lexical_map = {
        row["article_id"]: row
        for row in lexical_response.data
    }

    bias_reports = []
    for row in bias_response.data:
        source_data = row.pop("sources", None)
        source = SourceSummary(**source_data) if source_data else None
        article_id = row.get("article_id")
        lexical = lexical_map.get(article_id, {})

        bias_reports.append(BiasReportResponse(
            source=source,
            article_id=article_id,
            sentiment_label=row.get("sentiment_label"),
            sentiment_score=row.get("sentiment_score"),
            framing_score=row.get("framing_score"),
            divergent_words=lexical.get("divergent_words"),
            charged_words=lexical.get("charged_words"),
        ))

    return StoryClusterDetail(
        **cluster,
        articles=articles,
        bias_reports=bias_reports,
    )