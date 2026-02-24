import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { GlassPanel } from "@/components/GlassPanel";
import { StatusBadge, StatusType } from "@/components/StatusBadge";
import { ActionBadge, ActionType } from "@/components/ActionBadge";
import { LiquidProgress } from "@/components/LiquidProgress";
import { Pause, X, Maximize2, Camera, ChevronDown } from "lucide-react";

interface ExecutionAction {
  type: ActionType;
  target: string;
  value?: string;
  status: StatusType;
  duration: string;
  details?: string;
}

const MOCK_ACTIONS: ExecutionAction[] = [
  { type: "navigate", target: "https://app.example.com/signup", status: "success", duration: "1.2s", details: "Page loaded. DOM snapshot captured (3.2KB)." },
  { type: "fill", target: "input#email", value: "test@example.com", status: "success", duration: "0.3s", details: "Input validated client-side. No errors." },
  { type: "fill", target: "input#password", value: "••••••••", status: "success", duration: "0.2s", details: "Password strength: Strong." },
  { type: "select", target: "dropdown#country", value: "United States", status: "success", duration: "0.8s", details: "195 options found. Matched at index 184." },
  { type: "click", target: "input#terms-checkbox", status: "running", duration: "—", details: "Toggling checkbox state..." },
  { type: "click", target: "button#submit", status: "pending", duration: "—", details: "Queued. Will trigger POST /api/auth/register" },
  { type: "wait", target: "**/dashboard**", status: "pending", duration: "—", details: "Will wait up to 5000ms for redirect" },
  { type: "assert", target: "h1.welcome-text", status: "pending", duration: "—", details: "Will verify welcome message is visible" },
];

const NETWORK_LOG = [
  { method: "GET", url: "/api/config", status: 200, duration: "45ms" },
  { method: "GET", url: "/api/auth/session", status: 200, duration: "120ms" },
  { method: "POST", url: "/api/auth/register", status: 422, duration: "340ms" },
  { method: "POST", url: "/api/auth/register", status: 201, duration: "280ms" },
  { method: "GET", url: "/api/user/profile", status: 200, duration: "95ms" },
];

const CONSOLE_LOGS = [
  { type: "info", text: "Glass browser initialized", time: "00:00.100" },
  { type: "info", text: "Navigating to signup page...", time: "00:01.200" },
  { type: "info", text: "Filling email field", time: "00:02.300" },
  { type: "warn", text: "422 response from /api/auth/register", time: "00:04.100" },
  { type: "error", text: "Missing required field: terms_accepted", time: "00:04.200" },
  { type: "info", text: "Retrying with terms checkbox...", time: "00:05.500" },
  { type: "info", text: "POST /api/auth/register → 201 Created", time: "00:06.300" },
];

const Execute = () => {
  const [expandedAction, setExpandedAction] = useState<number | null>(null);
  const [elapsed, setElapsed] = useState(4.2);
  const [consoleFilter, setConsoleFilter] = useState<string>("all");

  const doneCount = MOCK_ACTIONS.filter(a => a.status === "success").length;
  const runningIndex = MOCK_ACTIONS.findIndex(a => a.status === "running");
  const progress = Math.round(((doneCount + 0.5) / MOCK_ACTIONS.length) * 100);

  useEffect(() => {
    const timer = setInterval(() => setElapsed(prev => +(prev + 0.1).toFixed(1)), 100);
    return () => clearInterval(timer);
  }, []);

  const filteredConsole = consoleFilter === "all" ? CONSOLE_LOGS : CONSOLE_LOGS.filter(l => l.type === consoleFilter);
  const networkErrors = NETWORK_LOG.filter(r => r.status >= 400).length;

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Command & Status Header */}
      <GlassPanel glow="cyan" delay={0}>
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div className="flex-1 min-w-0">
            <div className="font-mono text-xs text-muted-foreground mb-1">Command:</div>
            <pre className="font-mono text-sm text-foreground bg-muted/20 rounded-lg px-3 py-2 border border-glass-border whitespace-pre-wrap">
              Navigate to signup page, fill form with random data, select country, accept terms, submit
            </pre>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <button className="flex items-center gap-1.5 px-3 py-2 rounded-xl font-mono text-xs border border-amber-400/30 text-amber-400 hover:bg-amber-400/10 transition-colors">
              <Pause className="w-3 h-3" /> Pause
            </button>
            <button className="flex items-center gap-1.5 px-3 py-2 rounded-xl font-mono text-xs border border-destructive/30 text-destructive hover:bg-destructive/10 transition-colors animate-pulse">
              <X className="w-3 h-3" /> Cancel
            </button>
          </div>
        </div>
      </GlassPanel>

      {/* Status Banner */}
      <div className="glass-panel glass-glow-cyan p-5 flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center gap-4">
          <StatusBadge status="running" size="lg" />
          <div>
            <div className="font-mono text-2xl font-bold text-primary">{progress}%</div>
            <div className="font-mono text-[10px] text-muted-foreground">Action {doneCount + 1} of {MOCK_ACTIONS.length}</div>
          </div>
        </div>
        <div className="flex items-center gap-6">
          <div className="text-center">
            <div className="font-mono text-lg font-bold text-foreground">{elapsed}s</div>
            <div className="font-mono text-[9px] text-muted-foreground uppercase">Elapsed</div>
          </div>
          <div className="text-center">
            <div className="font-mono text-lg font-bold text-muted-foreground">~{(elapsed / progress * 100).toFixed(1)}s</div>
            <div className="font-mono text-[9px] text-muted-foreground uppercase">ETA</div>
          </div>
        </div>
      </div>

      {/* Progress Bar */}
      <LiquidProgress value={progress} label={`Executing: ${MOCK_ACTIONS[runningIndex]?.target || "..."}`} />

      {/* Three column layout */}
      <div className="grid lg:grid-cols-3 gap-6">
        {/* Action Timeline */}
        <GlassPanel title="Action Timeline" icon="📋" glow="cyan" delay={0.1}>
          <div className="space-y-1 max-h-[500px] overflow-y-auto">
            {MOCK_ACTIONS.map((action, i) => (
              <div key={i}>
                <div
                  onClick={() => setExpandedAction(expandedAction === i ? null : i)}
                  className={`flex items-center gap-2 px-2 py-2 rounded-lg cursor-pointer transition-colors text-xs font-mono ${
                    action.status === "running" ? "bg-primary/10 border border-primary/20" :
                    action.status === "success" ? "hover:bg-muted/10" :
                    "opacity-50 hover:opacity-70"
                  } ${expandedAction === i ? "ring-1 ring-primary/20" : ""}`}
                >
                  <StatusBadge status={action.status} className="border-0 bg-transparent px-0 gap-0" />
                  <ActionBadge type={action.type} />
                  <span className="truncate text-foreground/70 flex-1">{action.target}</span>
                  <span className="text-muted-foreground text-[10px] shrink-0">{action.duration}</span>
                </div>
                <AnimatePresence>
                  {expandedAction === i && action.details && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      className="overflow-hidden"
                    >
                      <div className="ml-6 my-1 px-3 py-2 rounded-lg border border-glass-border bg-muted/10 font-mono text-[11px] text-muted-foreground">
                        {action.details}
                        {action.value && <p className="text-primary/60 mt-1">Value: {action.value}</p>}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            ))}
          </div>
        </GlassPanel>

        {/* Browser Preview */}
        <GlassPanel title="Browser Preview" icon="🖥️" glow="purple" delay={0.2}>
          <div className="aspect-video bg-muted/20 rounded-xl border border-glass-border flex items-center justify-center relative overflow-hidden">
            <div className="text-center space-y-2">
              <span className="text-4xl animate-float">🌊</span>
              <p className="font-mono text-[11px] text-muted-foreground">Live preview updating...</p>
              <p className="font-mono text-[9px] text-primary animate-pulse">Capturing signup form</p>
            </div>
            <div className="absolute top-2 right-2 flex gap-1">
              <button className="p-1.5 rounded-lg bg-muted/30 text-muted-foreground hover:text-foreground transition-colors">
                <Camera className="w-3 h-3" />
              </button>
              <button className="p-1.5 rounded-lg bg-muted/30 text-muted-foreground hover:text-foreground transition-colors">
                <Maximize2 className="w-3 h-3" />
              </button>
            </div>
          </div>
          {/* Highlight overlay info */}
          <div className="mt-3 glass-panel-strong p-3 rounded-lg">
            <div className="font-mono text-[10px] text-muted-foreground">Currently targeting:</div>
            <div className="font-mono text-xs text-primary mt-1">input#terms-checkbox</div>
          </div>
        </GlassPanel>

        {/* Network Monitor */}
        <GlassPanel title="Network Monitor" icon="🔮" glow="cyan" delay={0.3}>
          <div className="flex items-center gap-3 mb-3">
            <span className="font-mono text-xs text-primary">{NETWORK_LOG.length} requests</span>
            <span className="font-mono text-xs text-destructive">{networkErrors} error{networkErrors !== 1 ? "s" : ""}</span>
          </div>
          <div className="space-y-1 max-h-[400px] overflow-y-auto">
            {NETWORK_LOG.map((req, i) => (
              <div key={i} className="flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-muted/10 transition-colors font-mono text-[11px]">
                <span className={`font-semibold w-10 ${req.method === "POST" ? "text-secondary" : "text-primary"}`}>{req.method}</span>
                <span className="truncate flex-1 text-foreground/70">{req.url}</span>
                <span className={req.status >= 400 ? "text-destructive" : req.status >= 300 ? "text-muted-foreground" : "text-emerald-400"}>{req.status}</span>
                <span className="text-muted-foreground w-12 text-right">{req.duration}</span>
              </div>
            ))}
          </div>
        </GlassPanel>
      </div>

      {/* Console Logs */}
      <GlassPanel title="Console Output" icon="🖥️" glow="none" delay={0.4}>
        <div className="flex items-center gap-2 mb-3">
          {["all", "info", "warn", "error"].map(f => (
            <button
              key={f}
              onClick={() => setConsoleFilter(f)}
              className={`font-mono text-[10px] px-2 py-1 rounded border transition-all capitalize ${
                consoleFilter === f ? "border-primary/40 bg-primary/10 text-primary" : "border-transparent text-muted-foreground hover:text-foreground"
              }`}
            >
              {f}
            </button>
          ))}
        </div>
        <div className="glass-panel-strong p-3 font-mono text-xs max-h-[200px] overflow-y-auto rounded-lg">
          <div className="flex items-center gap-2 mb-2 pb-2 border-b border-glass-border">
            <span className="w-2.5 h-2.5 rounded-full bg-destructive" />
            <span className="w-2.5 h-2.5 rounded-full bg-amber-400" />
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
            <span className="ml-2 text-muted-foreground text-[10px]">npm://console</span>
          </div>
          {filteredConsole.map((log, i) => (
            <div key={i} className="flex gap-2 py-0.5">
              <span className="text-muted-foreground shrink-0">[{log.time}]</span>
              <span className={
                log.type === "error" ? "text-destructive" :
                log.type === "warn" ? "text-amber-400" :
                "text-primary"
              }>{log.text}</span>
            </div>
          ))}
          <span className="inline-block w-2 h-4 bg-primary animate-terminal-blink ml-1" />
        </div>
      </GlassPanel>

      {/* AI Diagnosis (appears on error) */}
      <GlassPanel title="AI Diagnosis" icon="🧠" glow="pink" delay={0.5}>
        <div className="glass-panel-strong p-4 space-y-2">
          <div className="flex items-center justify-between">
            <span className="font-mono text-xs font-semibold text-foreground">Missing Required Field</span>
            <span className="font-mono text-[10px] font-bold text-destructive">Critical</span>
          </div>
          <div className="font-mono text-[11px] text-muted-foreground space-y-1">
            <p><span className="text-secondary">Component:</span> AuthController.register()</p>
            <p><span className="text-primary">🎯 Root Cause:</span> POST /api/auth/register returned 422. The 'terms_accepted' field was missing.</p>
            <p><span className="text-emerald-400">💡 Fix:</span> Add checkbox interaction for #terms-checkbox before submission.</p>
          </div>
          <div className="flex gap-2 mt-3">
            <button className="font-mono text-[10px] px-3 py-1.5 rounded-lg border border-primary/30 text-primary hover:bg-primary/10 transition-colors">
              View Full Diagnosis
            </button>
            <button className="font-mono text-[10px] px-3 py-1.5 rounded-lg border border-emerald-400/30 text-emerald-400 hover:bg-emerald-400/10 transition-colors">
              Retry with Fix
            </button>
          </div>
        </div>
      </GlassPanel>
    </div>
  );
};

export default Execute;
