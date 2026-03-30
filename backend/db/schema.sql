-- This table stores information about each news outlet we track
CREATE TABLE sources (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  name TEXT NOT NULL,                    -- e.g. "BBC News"
  url TEXT NOT NULL,                     -- Homepage URL
  rss_url TEXT,                          -- RSS feed URL if available
  country TEXT,                          -- e.g. "UK"
  known_lean TEXT,                       -- e.g. "centre-left" (optional, user-defined)
  is_active BOOLEAN DEFAULT TRUE,        -- Toggle sources on/off
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Each article fetched from any source gets a row here
CREATE TABLE articles (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  source_id UUID REFERENCES sources(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  body TEXT,                             -- Full article text if available
  summary TEXT,                          -- Short excerpt/description
  url TEXT UNIQUE NOT NULL,              -- Unique constraint prevents duplicates
  published_at TIMESTAMPTZ,
  category TEXT,                         -- Filled in Week 2 by ML model
  ai_score FLOAT,                        -- Filled in Week 2 by ML model
  embedding VECTOR(384),                 -- For story clustering (we'll enable this)
  fetched_at TIMESTAMPTZ DEFAULT NOW()
);

-- A "cluster" is a group of articles from different sources about the same event
CREATE TABLE story_clusters (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  canonical_headline TEXT,               -- Best representative headline for this story
  event_date DATE,
  category TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Many-to-many: one article belongs to one cluster, one cluster has many articles
CREATE TABLE cluster_articles (
  cluster_id UUID REFERENCES story_clusters(id) ON DELETE CASCADE,
  article_id UUID REFERENCES articles(id) ON DELETE CASCADE,
  PRIMARY KEY (cluster_id, article_id)   -- Prevents the same article being added twice
);

-- pgvector lets PostgreSQL store and compare vector embeddings
-- This is what powers our story clustering similarity search
CREATE EXTENSION IF NOT EXISTS vector;

INSERT INTO sources (name, url, rss_url, country, known_lean) VALUES
  ('BBC News', 'https://bbc.co.uk/news', 'http://feeds.bbci.co.uk/news/rss.xml', 'UK', 'centre'),
  ('The Guardian', 'https://theguardian.com', 'https://www.theguardian.com/world/rss', 'UK', 'centre-left'),
  ('Reuters', 'https://reuters.com', 'https://feeds.reuters.com/reuters/topNews', 'International', 'centre'),
  ('Al Jazeera', 'https://aljazeera.com', 'https://www.aljazeera.com/xml/rss/all.xml', 'International', 'centre'),
  ('The Telegraph', 'https://telegraph.co.uk', 'https://www.telegraph.co.uk/rss.xml', 'UK', 'centre-right');

-- Stores sentiment analysis results per article cluster
CREATE TABLE bias_reports (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  cluster_id UUID REFERENCES story_clusters(id) ON DELETE CASCADE,
  article_id UUID REFERENCES articles(id) ON DELETE CASCADE,
  source_id UUID REFERENCES sources(id) ON DELETE CASCADE,
  sentiment_label TEXT,     --'positive','negative','neutral'
  sentiment_score FLOAT,    -- confidence of the sentiment, 0.0-1.0
  bias_score FLOAT,         -- computed divergence score, filled lateral
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(cluster_id, article_id)  -- one report per article per cluster
);

-- Stores rolling bias profile per source, updated after each pipeline run
CREATE TABLE source_profiles (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  source_id UUID REFERENCES sources(id) ON DELETE CASCADE UNIQUE,
  avg_sentiment_score FLOAT DEFAULT 0.5,
  avg_bias_score FLOAT DEFAULT 0.0,
  total_articles_analysed INT DEFAULT 0,
  negative_pct FLOAT DEFAULT 0.0,         -- % of articles with negative sentiment
  positive_pct FLOAT DEFAULT 0.0,
  neutral_pct FLOAT DEFAULT 0.0,
  top_divergent_words TEXT[],             -- Array of words that diverge most from other sources
  last_updated TIMESTAMPTZ DEFAULT NOW()
);

-- Stores lexical framing results per article
CREATE TABLE lexical_frames (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  cluster_id UUID REFERENCES story_clusters(id) ON DELETE CASCADE,
  article_id UUID REFERENCES articles(id) ON DELETE CASCADE,
  source_id UUID REFERENCES sources(id) ON DELETE CASCADE,
  charged_words TEXT[],                 -- Words unique/prominent in this source's coverage
  divergent_words TEXT[],               -- Words used differently vs other sources in cluster
  framing_score FLOAT,                  -- 0-100, how different is this source's word choice
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(cluster_id, article_id)
);

-- Add a column to a story_clusters to store the overall divergence score
ALTER TABLE story_clusters ADD COLUMN IF NOT EXISTS divergence_score FLOAT;
ALTER TABLE story_clusters ADD COLUMN IF NOT EXISTS source_count INT DEFAULT 0;

-- Add coverage_asymmetry tracking to bias_reports
ALTER TABLE bias_reports ADD COLUMN IF NOT EXISTS framing_score FLOAT;

