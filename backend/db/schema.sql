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


