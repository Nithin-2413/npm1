import { motion } from "framer-motion";
import { useEffect, useState } from "react";

interface LiquidProgressProps {
  value: number;
  label?: string;
  showPercentage?: boolean;
}

export const LiquidProgress = ({ value, label, showPercentage = true }: LiquidProgressProps) => {
  const [displayed, setDisplayed] = useState(0);

  useEffect(() => {
    const timer = setTimeout(() => setDisplayed(value), 100);
    return () => clearTimeout(timer);
  }, [value]);

  const circumference = 2 * Math.PI * 42;
  const strokeOffset = circumference - (displayed / 100) * circumference;
  const glowColor = displayed >= 80 ? "hsl(var(--primary))" : displayed >= 50 ? "hsl(142 76% 56%)" : "hsl(38 92% 60%)";

  return (
    <div className="flex items-center gap-4">
      {/* Circular Progress */}
      <div className="relative w-24 h-24 shrink-0">
        <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
          {/* Background track */}
          <circle
            cx="50" cy="50" r="42"
            fill="none"
            stroke="hsl(var(--muted) / 0.3)"
            strokeWidth="6"
          />
          {/* Animated progress arc */}
          <motion.circle
            cx="50" cy="50" r="42"
            fill="none"
            stroke="url(#progressGradient)"
            strokeWidth="6"
            strokeLinecap="round"
            strokeDasharray={circumference}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset: strokeOffset }}
            transition={{ duration: 1.5, ease: "easeOut" }}
            style={{
              filter: `drop-shadow(0 0 6px ${glowColor})`,
            }}
          />
          {/* Gradient definition */}
          <defs>
            <linearGradient id="progressGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="hsl(var(--primary))" />
              <stop offset="50%" stopColor="hsl(var(--secondary))" />
              <stop offset="100%" stopColor="hsl(var(--primary))" />
            </linearGradient>
          </defs>
        </svg>

        {/* Center content */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          {showPercentage && (
            <motion.span
              key={displayed}
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              className="font-mono text-lg font-bold text-foreground"
            >
              {displayed}%
            </motion.span>
          )}
        </div>

        {/* Orbiting dot */}
        <motion.div
          className="absolute w-2 h-2 rounded-full"
          style={{
            background: glowColor,
            boxShadow: `0 0 8px ${glowColor}, 0 0 16px ${glowColor}`,
            top: "50%",
            left: "50%",
          }}
          animate={{
            rotate: 360,
          }}
          transition={{
            duration: 3,
            repeat: Infinity,
            ease: "linear",
          }}
          initial={false}
        >
          <div
            className="w-2 h-2 rounded-full"
            style={{
              transform: "translate(-50%, -50%) translateY(-42px)",
            }}
          />
        </motion.div>
      </div>

      {/* Label & status */}
      <div className="flex-1 min-w-0 space-y-1.5">
        {label && (
          <p className="font-mono text-[10px] text-muted-foreground uppercase tracking-wider truncate">
            {label}
          </p>
        )}
        <div className="flex items-center gap-2">
          <motion.div
            className="w-1.5 h-1.5 rounded-full"
            style={{ background: glowColor }}
            animate={{ opacity: [1, 0.4, 1] }}
            transition={{ duration: 1.2, repeat: Infinity }}
          />
          <span className="font-mono text-[11px] text-foreground/80">
            {displayed < 30 ? "Warming up..." : displayed < 60 ? "In progress" : displayed < 90 ? "Almost there" : "Finishing up"}
          </span>
        </div>
        {/* Mini linear track */}
        <div className="h-1 rounded-full bg-muted/30 overflow-hidden">
          <motion.div
            className="h-full rounded-full"
            style={{ background: `linear-gradient(90deg, ${glowColor}, hsl(var(--primary)))` }}
            initial={{ width: 0 }}
            animate={{ width: `${displayed}%` }}
            transition={{ duration: 1.5, ease: "easeOut" }}
          />
        </div>
      </div>
    </div>
  );
};
