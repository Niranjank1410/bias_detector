# backend/fetcher/test_feeds.py
"""
Quick script to test all RSS feeds and report which ones are working.
Run this whenever you add new sources.
"""

import feedparser
import time
from backend.db.client import supabase


def test_all_feeds():
    sources = supabase.table("sources").select("*").eq("is_active", True).execute().data

    print(f"Testing {len(sources)} sources...\n")

    working = []
    broken = []

    for source in sources:
        rss_url = source.get("rss_url")
        name = source["name"]

        if not rss_url:
            print(f"⚠️  {name}: No RSS URL configured")
            continue

        try:
            feed = feedparser.parse(rss_url)
            entry_count = len(feed.entries)

            if entry_count > 0:
                print(f"✅ {name}: {entry_count} entries")
                working.append(name)
            else:
                print(f"❌ {name}: Feed parsed but 0 entries ({rss_url})")
                broken.append(name)

        except Exception as e:
            print(f"❌ {name}: Error — {e}")
            broken.append(name)

        time.sleep(0.5)

    print(f"\n✅ Working: {len(working)}")
    print(f"❌ Broken: {len(broken)}")
    if broken:
        print(f"   Fix these: {', '.join(broken)}")


if __name__ == "__main__":
    test_all_feeds()