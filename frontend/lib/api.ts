// lib/api.ts
/**
 * Typed API client for the Bias Detector backend.
 * All data fetching goes through these functions.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// --- Types matching backend Pydantic models ---

export interface SourceSummary {
  id: string;
  name: string;
  country?: string;
  known_lean?: string;
}

export interface Article {
  id: string;
  title: string;
  summary?: string;
  url: string;
  published_at?: string;
  category?: string;
  ai_score?: number;
  source?: SourceSummary;
}

export interface BiasReport {
  source?: SourceSummary;
  article_id: string;
  sentiment_label?: string;
  sentiment_score?: number;
  framing_score?: number;
  divergent_words?: string[];
  charged_words?: string[];
}

export interface StoryCluster {
  id: string;
  canonical_headline: string;
  event_date?: string;
  category?: string;
  divergence_score?: number;
  source_count?: number;
}

export interface StoryClusterDetail extends StoryCluster {
  articles: Article[];
  bias_reports: BiasReport[];
}

export interface PaginatedStories {
  total: number;
  page: number;
  page_size: number;
  stories: StoryCluster[];
}

export interface SourceProfile {
  id: string;
  name: string;
  url?: string;
  country?: string;
  known_lean?: string;
  avg_sentiment_score?: number;
  avg_bias_score?: number;
  total_articles_analysed?: number;
  positive_pct?: number;
  negative_pct?: number;
  neutral_pct?: number;
  top_divergent_words?: string[];
}

export interface Category {
  category: string;
  article_count: number;
}

// --- API functions ---

async function fetchAPI<T>(path: string): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    next: { revalidate: 300 }, // Cache for 5 minutes
    signal: AbortSignal.timeout(35000), // 35s timeout to handle Render cold starts
  });
  if (!res.ok) throw new Error(`API error: ${res.status} ${path}`);
  return res.json();
}

export async function getStories(params?: {
  page?: number;
  page_size?: number;
  category?: string;
  min_sources?: number;
  search?: string;
}): Promise<PaginatedStories> {
  const query = new URLSearchParams();
  if (params?.page) query.set("page", String(params.page));
  if (params?.page_size) query.set("page_size", String(params.page_size));
  if (params?.category) query.set("category", params.category);
  if (params?.min_sources) query.set("min_sources", String(params.min_sources));
  const qs = query.toString();
  return fetchAPI(`/stories${qs ? `?${qs}` : ""}`);
}

export async function getStory(id: string): Promise<StoryClusterDetail> {
  return fetchAPI(`/stories/${id}`);
}

export async function getSources(): Promise<SourceProfile[]> {
  return fetchAPI("/sources");
}

export async function getCategories(): Promise<Category[]> {
  return fetchAPI("/categories");
}