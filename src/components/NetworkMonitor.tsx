import { motion } from "framer-motion";
import { GlassPanel } from "./GlassPanel";

interface NetworkRequest {
  method: string;
  url: string;
  status: number;
  duration: string;
  size: string;
}

const MOCK_REQUESTS: NetworkRequest[] = [
  { method: "GET", url: "/api/config", status: 200, duration: "45ms", size: "1.2KB" },
  { method: "GET", url: "/api/auth/session", status: 200, duration: "120ms", size: "0.8KB" },
  { method: "POST", url: "/api/auth/register", status: 422, duration: "340ms", size: "0.4KB" },
  { method: "POST", url: "/api/auth/register", status: 201, duration: "280ms", size: "1.1KB" },
  { method: "GET", url: "/api/user/profile", status: 200, duration: "95ms", size: "2.3KB" },
  { method: "GET", url: "/api/dashboard", status: 200, duration: "210ms", size: "5.6KB" },
  { method: "POST", url: "/api/analytics/event", status: 204, duration: "60ms", size: "0.0KB" },
  { method: "GET", url: "/assets/logo.svg", status: 304, duration: "12ms", size: "0.0KB" },
];

const statusColor = (status: number) => {
  if (status < 300) return "text-emerald-400";
  if (status < 400) return "text-muted-foreground";
  if (status < 500) return "text-amber-400";
  return "text-destructive";
};

const methodColor = (method: string) => {
  if (method === "GET") return "text-primary";
  if (method === "POST") return "text-glow-purple";
  if (method === "PUT") return "text-amber-400";
  if (method === "DELETE") return "text-destructive";
  return "text-muted-foreground";
};

export const NetworkMonitor = () => {
  return (
    <div className="font-mono text-xs space-y-1 max-h-[280px] overflow-y-auto">
      {/* Header */}
      <div className="grid grid-cols-[60px_1fr_60px_60px_60px] gap-2 text-muted-foreground pb-2 border-b border-glass-border text-[10px] uppercase tracking-wider">
        <span>Method</span>
        <span>URL</span>
        <span>Status</span>
        <span>Time</span>
        <span>Size</span>
      </div>
      {MOCK_REQUESTS.map((req, i) => (
        <motion.div
          key={i}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: i * 0.1 }}
          className="grid grid-cols-[60px_1fr_60px_60px_60px] gap-2 py-1.5 hover:bg-muted/20 rounded px-1 transition-colors"
        >
          <span className={`font-semibold ${methodColor(req.method)}`}>{req.method}</span>
          <span className="text-foreground/80 truncate">{req.url}</span>
          <span className={statusColor(req.status)}>{req.status}</span>
          <span className="text-muted-foreground">{req.duration}</span>
          <span className="text-muted-foreground">{req.size}</span>
        </motion.div>
      ))}
    </div>
  );
};
