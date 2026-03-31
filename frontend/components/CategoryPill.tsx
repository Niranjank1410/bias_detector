// components/CategoryPill.tsx
import clsx from "clsx";

const CATEGORY_COLOURS: Record<string, string> = {
  Politics: "text-accent-blue bg-accent-blue/10 border-accent-blue/20",
  Technology: "text-accent-purple bg-accent-purple/10 border-accent-purple/20",
  Business: "text-accent-yellow bg-accent-yellow/10 border-accent-yellow/20",
  Health: "text-accent-green bg-accent-green/10 border-accent-green/20",
  Science: "text-cyan-400 bg-cyan-400/10 border-cyan-400/20",
  Environment: "text-emerald-400 bg-emerald-400/10 border-emerald-400/20",
  Sport: "text-orange-400 bg-orange-400/10 border-orange-400/20",
  Entertainment: "text-pink-400 bg-pink-400/10 border-pink-400/20",
  Crime: "text-accent-red bg-accent-red/10 border-accent-red/20",
  "World News": "text-indigo-400 bg-indigo-400/10 border-indigo-400/20",
};

interface Props {
  category?: string | null;
  onClick?: () => void;
  active?: boolean;
}

export default function CategoryPill({ category, onClick, active }: Props) {
  if (!category) return null;
  const colour = CATEGORY_COLOURS[category] ?? "text-text-secondary bg-bg-tertiary border-bg-border";

  return (
    <span
      onClick={onClick}
      className={clsx(
        "inline-flex items-center text-xs font-medium px-2.5 py-1 rounded-full border",
        colour,
        onClick && "cursor-pointer hover:opacity-80",
        active && "ring-1 ring-current ring-offset-1 ring-offset-bg-primary"
      )}
    >
      {category}
    </span>
  );
}