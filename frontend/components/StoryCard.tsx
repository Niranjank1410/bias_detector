// components/StoryCard.tsx
"use client";

import Link from "next/link";
import { StoryCluster } from "@/lib/api";
import DivergenceScore from "./DivergenceScore";
import CategoryPill from "./CategoryPill";
import { Users, Calendar } from "lucide-react";

interface Props {
  story: StoryCluster;
  onCategoryClick?: (cat: string) => void;
}

export default function StoryCard({ story, onCategoryClick }: Props) {
  const date = story.event_date
    ? new Date(story.event_date).toLocaleDateString("en-GB", {
        day: "numeric", month: "short", year: "numeric",
      })
    : null;

  return (
    <Link href={`/story/${story.id}`}>
      <div className="group bg-bg-secondary border border-bg-border rounded-xl p-5 hover:border-accent-blue/30 hover:bg-bg-tertiary cursor-pointer">
        
        {/* Top row: category + divergence score */}
        <div className="flex items-center justify-between mb-3">
          <CategoryPill
            category={story.category}
            onClick={story.category && onCategoryClick
              ? (e) => { e?.stopPropagation?.(); onCategoryClick(story.category!); }
              : undefined
            }
          />
          <DivergenceScore score={story.divergence_score} />
        </div>

        {/* Headline */}
        <h3 className="text-text-primary font-semibold text-base leading-snug mb-3 group-hover:text-accent-blue line-clamp-2">
          {story.canonical_headline}
        </h3>

        {/* Bottom row: source count + date */}
        <div className="flex items-center gap-4 text-xs text-text-muted">
          {story.source_count != null && story.source_count > 1 && (
            <span className="flex items-center gap-1">
              <Users className="w-3 h-3" />
              {story.source_count} sources
            </span>
          )}
          {date && (
            <span className="flex items-center gap-1">
              <Calendar className="w-3 h-3" />
              {date}
            </span>
          )}
        </div>

        {/* Multi-source indicator bar */}
        {story.source_count != null && story.source_count > 1 && (
          <div className="mt-3 h-0.5 bg-bg-border rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-accent-blue to-accent-purple rounded-full"
              style={{ width: `${Math.min((story.divergence_score ?? 0), 100)}%` }}
            />
          </div>
        )}
      </div>
    </Link>
  );
}