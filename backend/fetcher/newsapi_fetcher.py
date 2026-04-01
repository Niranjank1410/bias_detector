# backend/fetcher/newsapi_fetcher.py
"""
Fetches articles from NewsAPI.

NewsAPI gives us structured JSON with title, description, source name,
URL, and published date. The free tier supports fetching top headlines 
and searching by keyword, with a limit of 100 requests/day.
"""

import os
from datetime import datetime, timezone
from newsapi import NewsApiClient
from dotenv import load_dotenv

load_dotenv()

newsapi = NewsApiClient(api_key=os.getenv("NEWSAPI_KEY"))

# These are the NewsAPI source IDs we want to pull from.
# Find more at: https://newsapi.org/docs/endpoints/sources
NEWSAPI_SOURCES = [
	"bbc-news",
	"reuters",
	"al-jazeera-english",
	"the-guardian-uk",
	"the-telegraph",
	"independant",
	"sky-news",
	"fox-news",
	"npr",
	"france24",
	"the-hindu",
	"dw-news"
]

def fetch_top_headlines() -> list[dict]:
	"""
	Fetches top headlines from the configured sources.
	Returns a list of article dicts, each containing:
	- title, summary, url, published_at, source_name
	"""

	articles = []

	# We fetch in batches per source because mixing sources in one
	# request can cause NewsAPI to sometimes drop some sources.

	for source_id in NEWSAPI_SOURCES:
		try:
			response = newsapi.get_top_headlines(
				sources = source_id,
				page_size = 20,			# Max is 100, but 20 per source is plenty
				language = "en",
			)
			
			if response.get("status") != "ok":
				print(f"[NewsAPI] Error for source {source_id}: {response}")
				continue

			for item in response.get("articles", []):
				# Skip articles with [Removed] content (NewsAPI placeholder)
				if item.get("title") == "[Removed]":
					continue
				
				# Normalize into internal format
				articles.append({
					"title": item.get("title", "").strip(),
					"summary": item.get("description", ""),
					"body": item.get("content", ""),	# Often truncated on the free tier
					"url": item.get("url", ""),
					"published_at": item.get("publishedAt"),	# ISO 8601 string
					"source_name": item["source"]["name"],
				})

		except Exception as e:
			print(f"[NewsAPI] Failed to fetch {source_id}: {e}")
			continue
	
	print(f"[NewsAPI] Fetched {len(articles)} articles total")
	return articles 
