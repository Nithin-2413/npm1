import { motion } from "framer-motion";

interface BlueprintStep {
  type: string;
  target: string;
  value?: string;
  status: "done" | "active" | "pending";
}

const MOCK_STEPS: BlueprintStep[] = [
  { type: "navigate", target: "https://app.example.com/signup", status: "done" },
  { type: "fill", target: "input#email", value: "{{USER_EMAIL}}", status: "done" },
  { type: "fill", target: "input#password", value: "{{PASSWORD}}", status: "done" },
  { type: "select", target: "dropdown#country", value: "United States", status: "done" },
  { type: "click", target: "input#terms-checkbox", status: "active" },
  { type: "click", target: "button#submit", status: "pending" },
  { type: "wait_for_url", target: "**/dashboard**", status: "pending" },
];

const statusStyles: Record<string, string> = {
  done: "border-emerald-400/40 bg-emerald-400/5",
  active: "border-primary/60 bg-primary/10",
  pending: "border-glass-border bg-transparent opacity-50",
};

const statusIcon: Record<string, string> = {
  done: "💎",
  active: "🌊",
  pending: "○",
};

export const BlueprintViewer = () => {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between mb-3">
        <span className="font-mono text-[10px] text-muted-foreground tracking-wider uppercase">
          Blueprint: signup_flow_v1
        </span>
        <span className="font-mono text-[10px] text-primary">5/7 steps</span>
      </div>

      {MOCK_STEPS.map((step, i) => (
        <motion.div
          key={i}
          initial={{ opacity: 0, x: -15 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: i * 0.08, duration: 0.4 }}
          className={`flex items-center gap-3 px-3 py-2 rounded-lg border font-mono text-xs ${statusStyles[step.status]}`}
        >
          <span className="text-sm">{statusIcon[step.status]}</span>
          <span className="text-glow-purple font-semibold w-20 shrink-0">{step.type}</span>
          <span className="text-foreground/70 truncate">{step.target}</span>
          {step.value && (
            <span className="ml-auto text-primary/80 shrink-0">→ {step.value}</span>
          )}
        </motion.div>
      ))}
    </div>
  );
};
