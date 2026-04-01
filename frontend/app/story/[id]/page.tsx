// app/story/[id]/page.tsx

"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { getStory, StoryClusterDetail } from "@/lib/api";
import DivergenceScore from "@/components/DivergenceScore";
import SentimentBadge from "@/components/SentimentBadge";
import AIScoreBadge from "@/components/AIScoreBadge";
import CategoryPill from "@/components/CategoryPill";
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis,
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis,
  Tooltip
} from "recharts";
import { ExternalLink, Loader2, ArrowLeft, Users } from "lucide-react";
import Link from "next/link";

const SENTIMENT_COLOUR: Record<string, string> = {
  positive: "#22c55e",
  negative: "#ef4444",
  neutral: "#5a5a72",
};

export default function StoryDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [story, setStory] = useState<StoryClusterDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    getStory(id)
      .then(setStory)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-32">
        <Loader2 className="w-6 h-6 animate-spin text-text-muted" />
      </div>
    );
  }

  if (!story) {
    return (
      <div className="text-center py-32 text-text-muted">Story not found.</div>
    );
  }

  const sentimentData = story.bias_reports.map((r) => ({
    source: r.source?.name?.replace(" News", "").replace(" English", "") ?? "Unknown",
    score: r.sentiment_score ? Math.round(r.sentiment_score * 100) : 0,
    label: r.sentiment_label ?? "neutral",
    framing: r.framing_score ? Math.round(r.framing_score) : 0,
  }));

  const radarData = story.bias_reports.map((r) => ({
    source: r.source?.name?.split(" ")[0] ?? "?",
    Sentiment: r.sentiment_score ? Math.round(r.sentiment_score * 100) : 50,
    Framing: r.framing_score ? Math.round(r.framing_score) : 0,
  }));

  return (
    <div className="max-w-4xl mx-auto">
      {/* Back button */}
      <Link
        href="/"
        className="inline-flex items-center gap-2 text-sm text-text-muted hover:text-text-primary mb-6"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to stories
      </Link>

      {/* Story header */}
      <div className="mb-8">
        <div className="flex flex-wrap items-center gap-2 mb-3">
          <CategoryPill category={story.category} />
          <div className="flex items-center gap-1.5">
            <DivergenceScore score={story.divergence_score} />
            <span className="text-xs text-text-muted" title="How differently sources covered this story. Higher = more disagreement.">
                ⓘ
            </span>
          </div>
          {story.event_date && (
            <span className="text-xs text-text-muted">
              {new Date(story.event_date).toLocaleDateString("en-GB", {
                day: "numeric",
                month: "long",
                year: "numeric",
              })}
            </span>
          )}
        </div>
        <h1 className="text-2xl font-bold text-text-primary leading-snug">
          {story.canonical_headline}
        </h1>
        <div className="flex items-center gap-3 mt-2">
          <span className="text-text-muted text-sm flex items-center gap-1.5">
            <Users className="w-3.5 h-3.5" />
            {story.source_count ?? story.articles.length} source{(story.source_count ?? 0) > 1 ? "s" : ""}
          </span>
          {(story.divergence_score ?? 0) > 30 && (
            <span className="text-xs text-accent-orange bg-accent-orange/10 border border-accent-orange/20 px-2 py-0.5 rounded-full">
              Highly contested
            </span>
          )}
          {(story.divergence_score ?? 0) <= 15 && (story.source_count ?? 0) > 1 && (
            <span className="text-xs text-accent-green bg-accent-green/10 border border-accent-green/20 px-2 py-0.5 rounded-full">
              Broad consensus
            </span>
          )}
        </div>
      </div>

      {/* Bias visualisation — only show if multiple sources */}
      {sentimentData.length > 1 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
          {/* Sentiment bar chart */}
          <div className="bg-bg-secondary border border-bg-border rounded-xl p-5">
            <h2 className="text-sm font-semibold text-text-secondary mb-4 uppercase tracking-wide">
              Sentiment by Source
            </h2>
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={sentimentData} layout="vertical">
                <XAxis
                  type="number"
                  domain={[0, 100]}
                  tick={{ fontSize: 10, fill: "#5a5a72" }}
                />
                <YAxis
                  dataKey="source"
                  type="category"
                  tick={{ fontSize: 11, fill: "#9090a8" }}
                  width={80}
                />
                <Tooltip
                  contentStyle={{
                    background: "#111118",
                    border: "1px solid #2a2a3a",
                    borderRadius: 8,
                    fontSize: 12,
                  }}
                  formatter={(val: unknown, _name: unknown, props: any) => [
                    `${val}% (${props?.payload?.label ?? ""})`,
                    "Sentiment",
                  ]}
                />
                <Bar
                  dataKey="score"
                  radius={[0, 4, 4, 0]}
                  fill="#4f8ef7"
                  shape={(props: any) => {
                    const { x, y, width, height, index } = props;
                    const entry = sentimentData[index];
                    const fill = SENTIMENT_COLOUR[entry?.label] ?? "#5a5a72";
                    return <rect x={x} y={y} width={width} height={height} fill={fill} rx={4} />;
                  }}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Framing score radar */}
          <div className="bg-bg-secondary border border-bg-border rounded-xl p-5">
            <h2 className="text-sm font-semibold text-text-secondary mb-4 uppercase tracking-wide">
              Framing Divergence
            </h2>
            <ResponsiveContainer width="100%" height={180}>
              <RadarChart data={radarData}>
                <PolarGrid stroke="#2a2a3a" />
                <PolarAngleAxis
                  dataKey="source"
                  tick={{ fontSize: 11, fill: "#9090a8" }}
                />
                <Radar
                  dataKey="Framing"
                  stroke="#4f8ef7"
                  fill="#4f8ef7"
                  fillOpacity={0.15}
                />
                <Radar
                  dataKey="Sentiment"
                  stroke="#8b5cf6"
                  fill="#8b5cf6"
                  fillOpacity={0.1}
                />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Per-source breakdown */}
      <div className="mb-8">
        <h2 className="text-sm font-semibold text-text-secondary uppercase tracking-wide mb-4">
          Coverage by Source
        </h2>
        <div className="space-y-3">
          {story.articles.map((article) => {
            const report = story.bias_reports.find(
              (r) => r.article_id === article.id
            );

            return (
              <div
                key={article.id}
                className="bg-bg-secondary border border-bg-border rounded-xl p-5"
              >
                {/* Source header */}
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-sm font-semibold text-text-primary">
                      {article.source?.name}
                    </span>
                    {article.source?.known_lean && (
                      <span className="text-xs text-text-muted border border-bg-border px-1.5 py-0.5 rounded">
                        {article.source.known_lean}
                      </span>
                    )}
                    {report && (
                      <SentimentBadge
                        label={report.sentiment_label}
                        score={report.sentiment_score}
                      />
                    )}
                    <AIScoreBadge score={article.ai_score} />
                  </div>
                  
                  < a href={article.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-text-muted hover:text-accent-blue"
                  >
                    <ExternalLink className="w-4 h-4" />
                  </a>
                </div>

                {/* Article title */}
                <p className="text-text-primary text-sm font-medium mb-2 leading-snug">
                  {article.title}
                </p>

                {/* Summary */}
                {article.summary && (
                  <p className="text-text-secondary text-xs leading-relaxed mb-3 line-clamp-2">
                    {article.summary}
                  </p>
                )}

                {/* Divergent + charged words */}
                {report?.divergent_words && report.divergent_words.length > 0 && (
                  <div className="mt-3">
                    <p className="text-xs text-text-muted mb-1.5">
                      Divergent language:
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      {report.divergent_words.slice(0, 8).map((word) => (
                        <span
                          key={word}
                          className="text-xs px-2 py-0.5 rounded bg-accent-blue/10 text-accent-blue border border-accent-blue/10"
                        >
                          {word}
                        </span>
                      ))}
                      {report.charged_words?.map((word) => (
                        <span
                          key={word}
                          className="text-xs px-2 py-0.5 rounded bg-accent-orange/10 text-accent-orange border border-accent-orange/10"
                        >
                          {word}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}