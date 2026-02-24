import { motion } from "framer-motion";

export type AvatarAnimal = "lion" | "puppy" | "peacock" | "dove" | "squirrel" | "panda";

interface AnimatedAvatarProps {
  animal: AvatarAnimal;
  size?: "sm" | "md" | "lg";
  selected?: boolean;
  onClick?: () => void;
}

const AVATAR_CONFIG: Record<AvatarAnimal, { emoji: string; label: string }> = {
  lion:     { emoji: "🦁", label: "Simba" },
  puppy:    { emoji: "🐶", label: "Buddy" },
  peacock:  { emoji: "🦚", label: "Plume" },
  dove:     { emoji: "🐰", label: "Bunny" },
  squirrel: { emoji: "🐿️", label: "Nutkin" },
  panda:    { emoji: "🐼", label: "Bamboo" },
};

const SIZE_CLASSES = {
  sm: "text-xl",
  md: "text-4xl",
  lg: "text-6xl",
};

export const AnimatedAvatar = ({ animal, size = "md", selected, onClick }: AnimatedAvatarProps) => {
  const config = AVATAR_CONFIG[animal];

  return (
    <motion.button
      type="button"
      onClick={onClick}
      whileHover={{
        scale: 1.15,
        rotate: [0, -5, 5, -3, 0],
        transition: { duration: 0.5, ease: "easeOut" },
      }}
      whileTap={{ scale: 0.9 }}
      className={`relative flex items-center justify-center cursor-pointer p-2 rounded-xl transition-colors duration-300 ${SIZE_CLASSES[size]} ${
        selected
          ? "bg-primary/10"
          : "bg-transparent hover:bg-muted/10"
      }`}
    >
      {/* Main emoji — breathing + subtle float */}
      <motion.span
        animate={{
          y: [0, -3, 0],
          scale: [1, 1.06, 1],
          rotate: [0, 1, 0, -1, 0],
        }}
        transition={{
          duration: 3,
          repeat: Infinity,
          ease: "easeInOut",
          delay: Math.random() * 1.5,
        }}
        className="select-none drop-shadow-lg"
        style={{
          filter: selected ? "drop-shadow(0 0 8px hsl(var(--primary) / 0.4))" : "drop-shadow(0 2px 4px hsl(0 0% 0% / 0.15))",
          transition: "filter 0.4s ease",
        }}
      >
        {config.emoji}
      </motion.span>

      {/* Selected indicator — soft underline glow */}
      {selected && (
        <motion.div
          className="absolute -bottom-1 left-1/2 h-[2px] rounded-full bg-primary"
          initial={{ width: 0, x: "-50%" }}
          animate={{
            width: "60%",
            x: "-50%",
            opacity: [0.6, 1, 0.6],
          }}
          transition={{
            width: { duration: 0.3, ease: "easeOut" },
            opacity: { duration: 2, repeat: Infinity },
          }}
        />
      )}
    </motion.button>
  );
};

export const AVATAR_ANIMALS: AvatarAnimal[] = ["lion", "puppy", "peacock", "dove", "squirrel", "panda"];

export const getAvatarLabel = (animal: AvatarAnimal) => AVATAR_CONFIG[animal].label;
export const getAvatarEmoji = (animal: AvatarAnimal) => AVATAR_CONFIG[animal].emoji;
