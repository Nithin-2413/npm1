import { motion } from "framer-motion";

interface StatCardProps {
  icon: string;
  label: string;
  value: string;
  subtext?: string;
  color: "cyan" | "purple" | "pink" | "green";
}

const colorMap = {
  cyan: "from-glow-cyan/20 to-transparent border-glow-cyan/30 text-primary",
  purple: "from-glow-purple/20 to-transparent border-glow-purple/30 text-secondary",
  pink: "from-glow-pink/20 to-transparent border-glow-pink/30 text-accent",
  green: "from-emerald-400/20 to-transparent border-emerald-400/30 text-emerald-400",
};

export const StatCard = ({ icon, label, value, subtext, color }: StatCardProps) => {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      whileHover={{ scale: 1.03, y: -2 }}
      transition={{ duration: 0.3 }}
      className={`glass-panel p-4 bg-gradient-to-br ${colorMap[color]} cursor-default`}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="font-mono text-[10px] tracking-wider uppercase text-muted-foreground mb-1">
            {label}
          </p>
          <p className="text-2xl font-bold font-mono">{value}</p>
          {subtext && (
            <p className="text-[10px] text-muted-foreground mt-1">{subtext}</p>
          )}
        </div>
        <span className="text-2xl animate-float">{icon}</span>
      </div>
    </motion.div>
  );
};
