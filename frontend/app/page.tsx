// app/page.tsx
"use client";

import { useState, useEffect, useCallback } from "react";
import { getStories, getCategories, PaginatedStories, Category } from "@/lib/api";
import StoryCard from "@/components/StoryCard";
import CategoryPill from "@/components/CategoryPill";
import { Search, Loader2, ChevronLeft, ChevronRight } from "lucide-react";
import clsx from "clsx";

export default function HomePage() {
  const [stories, setStories] = useState<PaginatedStories | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [multiSourceOnly, setMultiSourceOnly] = useState(false);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  // Fetch categories once on mount
  useEffect(() => {
    getCategories().then(setCategories).catch(console.error);
  }, []);

  // Fetch stories whenever filters change
  const fetchStories = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getStories({
        page,
        page_size: 20,
        category: selectedCategory ?? undefined,
        min_sources: multiSourceOnly ? 2 : 1,
        search: search || undefined,    //pass search to backend
      });

      setStories(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [page, selectedCategory, multiSourceOnly, search]);

  useEffect(() => { fetchStories(); }, [fetchStories]);

  // Reset page when filters change
  const handleCategorySelect = (cat: string) => {
    setSelectedCategory(prev => prev === cat ? null : cat);
    setPage(1);
  };

  const handleSearch = () => {
    setSearch(searchInput);
    setPage(1);
  };

  const totalPages = stories ? Math.ceil(stories.total / 20) : 1;

  return (
    <div>
      {/* Page header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-text-primary mb-1">
          Today's Stories
        </h1>
        <p className="text-text-secondary text-sm">
          News analysed for framing bias across {categories.length} categories
        </p>
      </div>
      {/* Stats bar */}
      {stories && (
        <div className="flex items-center gap-6 mb-6 p-4 bg-bg-secondary border border-bg-border rounded-xl">
          <div className="text-center">
            <div className="text-lg font-bold text-text-primary">{stories.total}</div>
            <div className="text-xs text-text-muted">Total Stories</div>
          </div>
          <div className="w-px h-8 bg-bg-border" />
          <div className="text-center">
            <div className="text-lg font-bold text-accent-blue">
              {categories.length}
            </div>
            <div className="text-xs text-text-muted">Categories</div>
          </div>
          <div className="w-px h-8 bg-bg-border" />
          <div className="text-center">
            <div className="text-lg font-bold text-accent-purple">
              {stories.stories.filter(s => (s.source_count ?? 0) > 1).length}
            </div>
            <div className="text-xs text-text-muted">Multi-source</div>
          </div>
          <div className="w-px h-8 bg-bg-border" />
          <div className="text-center">
            <div className="text-lg font-bold text-accent-orange">
              {stories.stories.filter(s => (s.divergence_score ?? 0) > 30).length}
            </div>
            <div className="text-xs text-text-muted">High Divergence</div>
          </div>
        </div>
      )}
      
      {/* Search bar */}
      <div className="flex gap-2 mb-6">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
          <input
            type="text"
            placeholder="Search headlines..."
            value={searchInput}
            onChange={e => setSearchInput(e.target.value)}
            onKeyDown={e => e.key === "Enter" && handleSearch()}
            className="w-full bg-bg-secondary border border-bg-border rounded-lg pl-9 pr-4 py-2.5 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent-blue/50"
          />
        </div>
        <button
          onClick={handleSearch}
          className="px-4 py-2.5 bg-accent-blue/10 border border-accent-blue/20 text-accent-blue text-sm font-medium rounded-lg hover:bg-accent-blue/20"
        >
          Search
        </button>
      </div>

      {/* Filter bar */}
      <div className="flex flex-wrap items-center gap-2 mb-6">
        {/* All categories button */}
        <button
          onClick={() => handleCategorySelect("")}
          className={clsx(
            "text-xs font-medium px-3 py-1.5 rounded-full border",
            !selectedCategory
              ? "bg-accent-blue/10 border-accent-blue/20 text-accent-blue"
              : "bg-bg-secondary border-bg-border text-text-secondary hover:text-text-primary"
          )}
        >
          All
        </button>

        {categories.map(c => (
          <CategoryPill
            key={c.category}
            category={c.category}
            onClick={() => handleCategorySelect(c.category)}
            active={selectedCategory === c.category}
          />
        ))}

        {/* Multi-source toggle */}
        <button
          onClick={() => { setMultiSourceOnly(p => !p); setPage(1); }}
          className={clsx(
            "ml-auto text-xs font-medium px-3 py-1.5 rounded-full border flex items-center gap-1.5",
            multiSourceOnly
              ? "bg-accent-purple/10 border-accent-purple/20 text-accent-purple"
              : "bg-bg-secondary border-bg-border text-text-secondary hover:text-text-primary"
          )}
        >
          <span className={clsx("w-1.5 h-1.5 rounded-full", multiSourceOnly ? "bg-accent-purple" : "bg-text-muted")} />
          Multi-source only
        </button>
      </div>

      {/* Stories grid */}
      {loading ? (
        <div className="flex flex-col items-center justify-center py-24 gap-3">
          <Loader2 className="w-6 h-6 text-text-muted animate-spin" />
          <p className="text-text-muted text-sm">Loading stories...</p>
          <p className="text-text-muted text-xs opacity-60">
            First load may take ~30s while the server wakes up
          </p>
        </div>
      ) : !stories?.stories.length ? (
        <div className="flex flex-col items-center justify-center py-24 gap-3">
          <div className="w-12 h-12 rounded-full bg-bg-secondary border border-bg-border flex items-center justify-center">
            <Search className="w-5 h-5 text-text-muted" />
          </div>
          <p className="text-text-primary font-medium">No stories found</p>
          <p className="text-text-muted text-sm text-center max-w-sm">
            {search
              ? `No headlines matching "${search}". Try different keywords.`
              : selectedCategory
              ? `No ${selectedCategory} stories yet. Try a different category.`
              : "No stories available yet. Run the pipeline to fetch articles."}
          </p>
          {(search || selectedCategory) && (
            <button
              onClick={() => { setSearch(""); setSearchInput(""); setSelectedCategory(null); }}
              className="text-sm text-accent-blue hover:underline mt-1"
            >
              Clear filters
            </button>
          )}
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
            {stories.stories.map(story => (
              <StoryCard
                key={story.id}
                story={story}
                onCategoryClick={handleCategorySelect}
              />
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-3">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="p-2 rounded-lg border border-bg-border text-text-secondary hover:text-text-primary disabled:opacity-30"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span className="text-sm text-text-secondary">
                Page {page} of {totalPages}
              </span>
              <button
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="p-2 rounded-lg border border-bg-border text-text-secondary hover:text-text-primary disabled:opacity-30"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}