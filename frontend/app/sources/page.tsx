// app/sources/page.tsx
"use client";

import { useEffect, useState } from "react";
import { getSources, SourceProfile } from "@/lib/api";
import { Loader2, ExternalLink } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip, Cell } from "recharts";

const LEAN_COLOUR: Record<string, string> = {
  "centre-left": "#4f8ef7",
  "centre": "#9090a8",
  "centre-right": "#f97316",
  "left": "#8b5cf6",
  "right": "#ef4444",
};

export default function SourcesPage() {
  const [sources, setSources] = useState<SourceProfile[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getSources()
      .then(setSources)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="flex items-center justify-center py-32">
      <Loader2 className="w-6 h-6 animate-spin text-text-muted" />
    </div>
  );

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-text-primary mb-1">Source Profiles</h1>
        <p className="text-text-secondary text-sm">
          Rolling bias analysis based on accumulated coverage data
        </p>
      </div>

      {/* Sentiment comparison chart */}
      <div className="bg-bg-secondary border border-bg-border rounded-xl p-6 mb-8">
        <h2 className="text-sm font-semibold text-text-secondary uppercase tracking-wide mb-5">
          Sentiment Distribution by Source
        </h2>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart
            data={sources.filter(s => s.total_articles_analysed).map(s => ({
              name: s.name.replace(" News", "").replace(" English", ""),
              Positive: s.positive_pct ?? 0,
              Neutral: s.neutral_pct ?? 0,
              Negative: s.negative_pct ?? 0,
            }))}
          >
            <XAxis dataKey="name" tick={{ fontSize: 11, fill: "#9090a8" }} />
            <YAxis tick={{ fontSize: 10, fill: "#5a5a72" }} unit="%" />
            <Tooltip
              contentStyle={{ background: "#111118", border: "1px solid #2a2a3a", borderRadius: 8, fontSize: 12 }}
              formatter={(val: unknown) => `${(val as number).toFixed(1)}%`}
            />
            <Bar dataKey="Positive" stackId="a" fill="#22c55e" radius={[0, 0, 0, 0]} />
            <Bar dataKey="Neutral" stackId="a" fill="#2a2a3a" />
            <Bar dataKey="Negative" stackId="a" fill="#ef4444" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
        {/* Legend */}
        <div className="flex items-center gap-4 mt-3 justify-center text-xs text-text-muted">
          {[["#22c55e", "Positive"], ["#2a2a3a", "Neutral"], ["#ef4444", "Negative"]].map(([c, l]) => (
            <span key={l} className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-sm" style={{ background: c }} />
              {l}
            </span>
          ))}
        </div>
      </div>

      {/* Source cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {sources.map(source => (
          <div key={source.id} className="bg-bg-secondary border border-bg-border rounded-xl p-5">
            {/* Header */}
            <div className="flex items-start justify-between mb-4">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="font-semibold text-text-primary">{source.name}</h3>
                  {source.url && (
                    <a href={source.url} target="_blank" rel="noopener noreferrer"
                      className="text-text-muted hover:text-accent-blue">
                      <ExternalLink className="w-3.5 h-3.5" />
                    </a>
                  )}
                </div>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-xs text-text-muted">{source.country}</span>
                  {source.known_lean && (
                    <span
                      className="text-xs px-2 py-0.5 rounded-full border"
                      style={{
                        color: LEAN_COLOUR[source.known_lean] ?? "#9090a8",
                        borderColor: `${LEAN_COLOUR[source.known_lean] ?? "#9090a8"}33`,
                        background: `${LEAN_COLOUR[source.known_lean] ?? "#9090a8"}11`,
                      }}
                    >
                      {source.known_lean}
                    </span>
                  )}
                </div>
              </div>
              <div className="text-right">
                <div className="text-lg font-bold text-text-primary">
                  {source.avg_bias_score?.toFixed(1) ?? "—"}
                </div>
                <div className="text-xs text-text-muted">avg bias score</div>
              </div>
            </div>

            {/* Stats */}
            {source.total_articles_analysed ? (
              <>
                <div className="text-xs text-text-muted mb-2">
                  {source.total_articles_analysed} articles analysed
                </div>

                {/* Sentiment bar */}
                <div className="flex h-2 rounded-full overflow-hidden mb-3">
                  <div style={{ width: `${source.positive_pct ?? 0}%`, background: "#22c55e" }} />
                  <div style={{ width: `${source.neutral_pct ?? 0}%`, background: "#2a2a3a" }} />
                  <div style={{ width: `${source.negative_pct ?? 0}%`, background: "#ef4444" }} />
                </div>
                <div className="flex justify-between text-xs text-text-muted">
                  <span className="text-accent-green">{source.positive_pct?.toFixed(0)}% positive</span>
                  <span>{source.neutral_pct?.toFixed(0)}% neutral</span>
                  <span className="text-accent-red">{source.negative_pct?.toFixed(0)}% negative</span>
                </div>

                {/* Top divergent words */}
                {source.top_divergent_words && source.top_divergent_words.length > 0 && (
                  <div className="mt-4">
                    <p className="text-xs text-text-muted mb-2">Characteristic language:</p>
                    <div className="flex flex-wrap gap-1.5">
                      {source.top_divergent_words.slice(0, 8).map(word => (
                        <span key={word} className="text-xs px-2 py-0.5 rounded bg-bg-tertiary text-text-secondary border border-bg-border">
                          {word}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </>
            ) : (
              <p className="text-xs text-text-muted">No data yet — run the pipeline to populate.</p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}