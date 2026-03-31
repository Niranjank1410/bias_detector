// components/SentimentBadge.tsx
import clsx from "clsx";

interface Props {
  label?: string;
  score?: number;
}

export default function SentimentBadge({ label, score }: Props) {
  if (!label) return null;

  const styles = {
    positive: "text-accent-green bg-accent-green/10 border-accent-green/20",
    negative: "text-accent-red bg-accent-red/10 border-accent-red/20",
    neutral: "text-text-secondary bg-bg-tertiary border-bg-border",
  };

  const style = styles[label as keyof typeof styles] ?? styles.neutral;

  return (
    <span className={clsx(
      "inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded border capitalize",
      style
    )}>
      {label}
      {score != null && (
        <span className="opacity-60">{(score * 100).toFixed(0)}%</span>
      )}
    </span>
  );
}