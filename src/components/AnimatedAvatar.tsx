import { motion } from "framer-motion";

export type AvatarAnimal = "lion" | "puppy" | "peacock" | "dove" | "squirrel" | "panda";

interface AnimatedAvatarProps {
  animal: AvatarAnimal;
  size?: "sm" | "md" | "lg";
  selected?: boolean;
  onClick?: () => void;
}

const AVATAR_CONFIG: Record<AvatarAnimal, { emoji: string; bg: string; label: string }> = {
  lion:     { emoji: "🦁", bg: "from-amber-400/30 to-orange-500/30",   label: "Simba" },
  puppy:    { emoji: "🐶", bg: "from-yellow-300/30 to-amber-400/30",   label: "Buddy" },
  peacock:  { emoji: "🦚", bg: "from-teal-400/30 to-emerald-500/30",   label: "Plume" },
  dove:     { emoji: "🕊️", bg: "from-sky-300/30 to-indigo-400/30",     label: "Grace" },
  squirrel: { emoji: "🐿️", bg: "from-orange-300/30 to-red-400/30",     label: "Nutkin" },
  panda:    { emoji: "🐼", bg: "from-slate-300/30 to-zinc-500/30",     label: "Bamboo" },
};

const SIZE_CLASSES = {
  sm: "w-7 h-7 text-sm",
  md: "w-14 h-14 text-2xl",
  lg: "w-20 h-20 text-4xl",
};

export const AnimatedAvatar = ({ animal, size = "md", selected, onClick }: AnimatedAvatarProps) => {
  const config = AVATAR_CONFIG[animal];

  return (
    <motion.button
      type="button"
      onClick={onClick}
      whileHover={{ scale: 1.1 }}
      whileTap={{ scale: 0.95 }}
      className={`relative rounded-2xl bg-gradient-to-br ${config.bg} flex items-center justify-center cursor-pointer transition-all duration-200 ${SIZE_CLASSES[size]} ${
        selected
          ? "ring-2 ring-primary ring-offset-2 ring-offset-background shadow-lg"
          : "border border-glass-border hover:border-primary/30"
      }`}
      style={{
        backdropFilter: "blur(12px)",
      }}
    >
      {/* Breathing animation */}
      <motion.span
        animate={{
          y: [0, -2, 0],
          scale: [1, 1.05, 1],
        }}
        transition={{
          duration: 2.5,
          repeat: Infinity,
          ease: "easeInOut",
          delay: Math.random() * 1.5,
        }}
        className="select-none"
      >
        {config.emoji}
      </motion.span>

      {/* Subtle glow ring on selected */}
      {selected && (
        <motion.div
          className="absolute inset-0 rounded-2xl"
          animate={{ opacity: [0.3, 0.6, 0.3] }}
          transition={{ duration: 2, repeat: Infinity }}
          style={{
            boxShadow: "0 0 20px 4px hsl(var(--primary) / 0.2)",
          }}
        />
      )}
    </motion.button>
  );
};

export const AVATAR_ANIMALS: AvatarAnimal[] = ["lion", "puppy", "peacock", "dove", "squirrel", "panda"];

export const getAvatarLabel = (animal: AvatarAnimal) => AVATAR_CONFIG[animal].label;
export const getAvatarEmoji = (animal: AvatarAnimal) => AVATAR_CONFIG[animal].emoji;
