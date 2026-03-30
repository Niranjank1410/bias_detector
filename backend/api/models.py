# backend/api/models.py
"""
Pydantic response models for the API.

These define the exact JSON structure returned by each endpoint.
FastAPI uses these to:
1. Validate that your DB data matches the expected shape
2. Auto-generate the /docs page with full API documentation
3. Serialise Python objects into JSON automatically
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date


class SourceSummary(BaseModel):
    """Minimal source info embedded in article/story responses."""
    id: str
    name: str
    country: Optional[str] = None
    known_lean: Optional[str] = None

class ArticleResponse(BaseModel):
    """A single article with it's ML-generated fields."""
    id: str
    title: str
    summary: Optional[str] = None
    url: str
    published_at: Optional[datetime] = None
    category: Optional[str] = None
    ai_score: Optional[str] = None
    source: Optional[SourceSummary] = None

class BiasReportResponse(BaseModel):
    """Sentiment + framing data for one article within a cluster."""
    source: SourceSummary
    article_id: str
    sentiment_label: Optional[str] = None
    sentiment_score: Optional[float] = None
    framing_score: Optional[float] = None
    divergent_words: Optional[list[str]] = None
    charged_words: Optional[list[str]] = None

class StoryClusterSummary(BaseModel):
    """Summary of a story cluster for the home page list."""
    id: str
    canonical_headline: str
    event_data: Optional[date] = None
    category: Optional[str] = None
    divergence_score: Optional[float] = None
    source_count: Optional[int] = None

class StoryClusterDetail(BaseModel):
    """Full story cluster detail including all source coverage."""
    id: str
    canonical_headline: str
    event_date: Optional[date] = None
    category: Optional[str] = None
    divergence_score: Optional[float] = None
    source_count: Optional[int] = None
    articles: list[ArticleResponse] = []
    bias_reports: list[BiasReportResponse] = []

class SourceProfile(BaseModel):
    """Full source profile with rolling bias statistics."""
    id: str
    name: str
    url: Optional[str] = None
    country: Optional[str] = None
    known_lean: Optional[str] = None
    avg_sentiment_score: Optional[float] = None
    avg_bias_score: Optional[float] = None
    total_articles_analysed: Optional[int] = None
    positive_pct: Optional[float] = None
    negative_pct: Optional[float] = None
    neutral_pct: Optional[float] = None
    top_divergent_words: Optional[list[str]] = None

class CategorySummary(BaseModel):
    """A category with its article count."""
    category: str
    article_count: int

class PaginatedStories(BaseModel):
    """Paginated list of story clusters."""
    total: int
    page: int
    page_size: int
    stories: list[StoryClusterSummary]