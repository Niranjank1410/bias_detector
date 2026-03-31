// components/AIScoreBadge.tsx
import clsx from "clsx";

interface Props {
  score?: number | null;
}

export default function AIScoreBadge({ score }: Props) {
  if (score == null) return null;

  const isAI = score > 0.6;
  const isUncertain = score >= 0.3 && score <= 0.6;

  return (
    <span
      title={`AI probability: ${(score * 100).toFixed(0)}%`}
      className={clsx(
        "inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded border",
        isAI
          ? "text-accent-red bg-accent-red/10 border-accent-red/20"
          : isUncertain
          ? "text-accent-yellow bg-accent-yellow/10 border-accent-yellow/20"
          : "text-accent-green bg-accent-green/10 border-accent-green/20"
      )}
    >
      {isAI ? "Likely AI" : isUncertain ? "Uncertain" : "Human"}
      <span className="opacity-60">{(score * 100).toFixed(0)}%</span>
    </span>
  );
}