import { useState, useEffect } from "react";
import { motion } from "framer-motion";

interface SystemPulseProps {
  className?: string;
}

export const SystemPulse = ({ className = "" }: SystemPulseProps) => {
  const [metrics, setMetrics] = useState({
    cpu: 42,
    memory: 61,
    requests: 12,
    uptime: "99.9%",
  });

  // Simulate live metric changes
  useEffect(() => {
    const timer = setInterval(() => {
      setMetrics(prev => ({
        cpu: Math.min(100, Math.max(10, prev.cpu + (Math.random() - 0.5) * 15)),
        memory: Math.min(100, Math.max(30, prev.memory + (Math.random() - 0.5) * 8)),
        requests: Math.max(0, Math.round(prev.requests + (Math.random() - 0.3) * 5)),
        uptime: "99.9%",
      }));
    }, 2000);
    return () => clearInterval(timer);
  }, []);

  const getBarColor = (value: number) => {
    if (value < 50) return "bg-emerald-400";
    if (value < 80) return "bg-amber-400";
    return "bg-destructive";
  };

  return (
    <div className={`space-y-2.5 ${className}`}>
      <div className="flex items-center gap-2 mb-1">
        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
        <span className="font-mono text-[9px] text-muted-foreground uppercase tracking-wider">System Pulse</span>
      </div>

      {[
        { label: "CPU", value: Math.round(metrics.cpu) },
        { label: "MEM", value: Math.round(metrics.memory) },
      ].map(({ label, value }) => (
        <div key={label} className="space-y-0.5">
          <div className="flex items-center justify-between">
            <span className="font-mono text-[9px] text-muted-foreground">{label}</span>
            <span className="font-mono text-[9px] text-foreground/70">{value}%</span>
          </div>
          <div className="h-1 rounded-full bg-muted/30 overflow-hidden">
            <motion.div
              className={`h-full rounded-full ${getBarColor(value)}`}
              animate={{ width: `${value}%` }}
              transition={{ duration: 0.8, ease: "easeOut" }}
            />
          </div>
        </div>
      ))}

      <div className="flex items-center justify-between pt-1">
        <span className="font-mono text-[9px] text-muted-foreground">REQ/s</span>
        <span className="font-mono text-[9px] text-primary font-bold">{metrics.requests}</span>
      </div>
      <div className="flex items-center justify-between">
        <span className="font-mono text-[9px] text-muted-foreground">Uptime</span>
        <span className="font-mono text-[9px] text-emerald-400">{metrics.uptime}</span>
      </div>
    </div>
  );
};
