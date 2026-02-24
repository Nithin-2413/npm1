import { cn } from "@/lib/utils";

export type ActionType = "navigate" | "fill" | "click" | "select" | "wait" | "assert" | "screenshot" | "custom";

const ACTION_MAP: Record<ActionType, { color: string; icon: string }> = {
  navigate: { color: "text-primary border-primary/30 bg-primary/10", icon: "🧭" },
  fill: { color: "text-secondary border-secondary/30 bg-secondary/10", icon: "✏️" },
  click: { color: "text-emerald-400 border-emerald-400/30 bg-emerald-400/10", icon: "👆" },
  select: { color: "text-amber-400 border-amber-400/30 bg-amber-400/10", icon: "🔽" },
  wait: { color: "text-muted-foreground border-glass-border bg-muted/10", icon: "⏳" },
  assert: { color: "text-accent border-accent/30 bg-accent/10", icon: "✓" },
  screenshot: { color: "text-primary border-primary/30 bg-primary/10", icon: "📸" },
  custom: { color: "text-muted-foreground border-glass-border bg-muted/10", icon: "⚙️" },
};

interface ActionBadgeProps {
  type: ActionType;
  className?: string;
}

export const ActionBadge = ({ type, className }: ActionBadgeProps) => {
  const config = ACTION_MAP[type] || ACTION_MAP.custom;
  return (
    <span className={cn(
      "font-mono text-[10px] font-semibold px-2 py-0.5 rounded border inline-flex items-center gap-1",
      config.color,
      className
    )}>
      <span>{config.icon}</span>
      <span className="uppercase">{type}</span>
    </span>
  );
};
