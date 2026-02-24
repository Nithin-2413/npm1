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

  return (
    <div className="space-y-2">
      {(label || showPercentage) && (
        <div className="flex justify-between font-mono text-xs">
          {label && <span className="text-muted-foreground">{label}</span>}
          {showPercentage && <span className="text-primary">{displayed}%</span>}
        </div>
      )}
      <div className="h-2.5 rounded-full bg-muted/50 overflow-hidden">
        <motion.div
          className="liquid-bar h-full"
          initial={{ width: 0 }}
          animate={{ width: `${displayed}%` }}
          transition={{ duration: 1.5, ease: "easeOut" }}
        />
      </div>
    </div>
  );
};
