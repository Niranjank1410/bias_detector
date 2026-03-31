// components/DivergenceScore.tsx
/**
 * Visual indicator for a story's divergence score.
 * 0-30: Low (grey) — sources broadly agree
 * 31-60: Medium (yellow) — noticeable framing differences
 * 61-100: High (red) — significant disagreement
 */

import clsx from "clsx";

interface Props {
  score?: number | null;
  showLabel?: boolean;
}

export default function DivergenceScore({ score, showLabel = true }: Props) {
  if (score == null) return null;

  const level = score > 60 ? "high" : score > 30 ? "medium" : "low";

  const colours = {
    low: "text-text-secondary border-bg-border",
    medium: "text-accent-yellow border-accent-yellow/30 bg-accent-yellow/5",
    high: "text-accent-red border-accent-red/30 bg-accent-red/5",
  };

  const labels = { low: "Low Bias", medium: "Medium Bias", high: "High Bias" };
  const dots = { low: "bg-text-muted", medium: "bg-accent-yellow", high: "bg-accent-red" };

  return (
    <span className={clsx(
      "inline-flex items-center gap-1.5 text-xs font-medium px-2 py-1 rounded-full border",
      colours[level]
    )}>
      <span className={clsx("w-1.5 h-1.5 rounded-full", dots[level])} />
      {score.toFixed(0)}
      {showLabel && <span className="opacity-70">{labels[level]}</span>}
    </span>
  );
}