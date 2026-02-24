import { memo } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";
import { ActionBadge, ActionType } from "@/components/ActionBadge";
import { cn } from "@/lib/utils";

export interface FlowActionData {
  [key: string]: unknown;
  actionId: string;
  type: ActionType;
  selector: string;
  value: string;
  timeout: number;
  optional: boolean;
  isViewMode?: boolean;
}

type FlowActionNodeProps = NodeProps & { data: FlowActionData };

export const FlowActionNode = memo(({ data, selected }: FlowActionNodeProps) => {
  const label = data.selector || data.value || "(empty)";

  return (
    <div
      className={cn(
        "px-4 py-3 rounded-xl border backdrop-blur-sm min-w-[180px] max-w-[260px] transition-all cursor-grab active:cursor-grabbing",
        selected
          ? "border-primary/50 bg-primary/10 ring-2 ring-primary/20 shadow-[0_0_20px_hsl(var(--primary)/0.15)]"
          : "border-glass-border bg-[hsl(var(--glass-bg))] hover:border-primary/30 hover:shadow-[0_0_12px_hsl(var(--primary)/0.08)]"
      )}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="!w-3 !h-3 !bg-primary/60 !border-2 !border-primary/30 !-top-1.5"
      />
      <div className="flex items-center gap-2.5">
        <ActionBadge type={data.type} />
        <div className="flex-1 min-w-0">
          <div className="font-mono text-[11px] text-foreground/90 truncate">{label}</div>
          {data.optional && (
            <span className="font-mono text-[8px] text-muted-foreground/60 uppercase">optional</span>
          )}
        </div>
      </div>
      <Handle
        type="source"
        position={Position.Bottom}
        className="!w-3 !h-3 !bg-primary/60 !border-2 !border-primary/30 !-bottom-1.5"
      />
    </div>
  );
});

FlowActionNode.displayName = "FlowActionNode";

export const StartNode = memo(() => (
  <div className="px-5 py-2.5 rounded-xl bg-emerald-400/10 border border-emerald-400/30 shadow-[0_0_15px_hsl(150_80%_40%/0.1)]">
    <span className="text-emerald-400 font-mono text-xs font-bold tracking-wider">▶ START</span>
    <Handle
      type="source"
      position={Position.Bottom}
      className="!w-3 !h-3 !bg-emerald-400/60 !border-2 !border-emerald-400/30 !-bottom-1.5"
    />
  </div>
));

StartNode.displayName = "StartNode";

export const EndNode = memo(() => (
  <div className="px-5 py-2.5 rounded-xl bg-destructive/10 border border-destructive/30 shadow-[0_0_15px_hsl(0_80%_55%/0.1)]">
    <Handle
      type="target"
      position={Position.Top}
      className="!w-3 !h-3 !bg-destructive/60 !border-2 !border-destructive/30 !-top-1.5"
    />
    <span className="text-destructive font-mono text-xs font-bold tracking-wider">■ END</span>
  </div>
));

EndNode.displayName = "EndNode";
