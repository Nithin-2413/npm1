import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { AnimatedAvatar, AVATAR_ANIMALS, AvatarAnimal, getAvatarLabel } from "@/components/AnimatedAvatar";
import { motion } from "framer-motion";
import { ChevronRight, Sparkles } from "lucide-react";

const ROLES = [
  { value: "qa_engineer", label: "QA Engineer", icon: "🧪" },
  { value: "developer", label: "Developer", icon: "💻" },
  { value: "team_lead", label: "Team Lead", icon: "👑" },
  { value: "devops", label: "DevOps", icon: "⚙️" },
  { value: "product_manager", label: "Product Manager", icon: "📋" },
  { value: "designer", label: "Designer", icon: "🎨" },
];

const Onboarding = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [selectedAvatar, setSelectedAvatar] = useState<AvatarAnimal>("lion");
  const [displayName, setDisplayName] = useState(user?.name || "");
  const [role, setRole] = useState("");
  const [email] = useState(user?.email || "");

  const handleFinish = () => {
    // Persist choices
    localStorage.setItem("npm_avatar", selectedAvatar);
    localStorage.setItem("npm_display_name", displayName);
    localStorage.setItem("npm_role", role);
    localStorage.setItem("npm_onboarded", "true");
    window.dispatchEvent(new CustomEvent("avatar-changed", { detail: selectedAvatar }));
    navigate("/");
  };

  const isValid = selectedAvatar && displayName.trim() && role;

  return (
    <div className="min-h-screen bg-background flex items-center justify-center relative overflow-hidden">
      {/* Background orbs */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden z-0">
        <div className="absolute top-[-20%] left-[-10%] w-[500px] h-[500px] rounded-full bg-primary/5 blur-[120px] animate-pulse-glow" />
        <div className="absolute top-[30%] right-[-10%] w-[600px] h-[600px] rounded-full bg-secondary/5 blur-[120px] animate-pulse-glow" style={{ animationDelay: "1s" }} />
        <div className="absolute bottom-[-10%] left-[30%] w-[400px] h-[400px] rounded-full bg-accent/5 blur-[120px] animate-pulse-glow" style={{ animationDelay: "2s" }} />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative z-10 w-full max-w-lg mx-4"
      >
        {/* Header */}
        <div className="text-center mb-6">
          <span className="text-4xl animate-float inline-block">🌊</span>
          <h1 className="text-2xl font-black tracking-tight gradient-text mt-3">Welcome aboard!</h1>
          <p className="font-mono text-[10px] text-muted-foreground tracking-widest uppercase mt-1">
            Let's set up your profile
          </p>
        </div>

        <div className="glass-panel-strong p-8 rounded-2xl space-y-6">
          {/* Avatar Selection */}
          <div>
            <label className="font-mono text-[10px] text-muted-foreground uppercase tracking-wider flex items-center gap-1.5 mb-3">
              <Sparkles className="w-3 h-3" /> Pick your avatar
            </label>
            <div className="flex flex-wrap gap-3 justify-center">
              {AVATAR_ANIMALS.map((animal) => (
                <div key={animal} className="flex flex-col items-center gap-1">
                  <AnimatedAvatar
                    animal={animal}
                    size="md"
                    selected={selectedAvatar === animal}
                    onClick={() => setSelectedAvatar(animal)}
                  />
                  <span className={`font-mono text-[8px] ${selectedAvatar === animal ? "text-primary font-semibold" : "text-muted-foreground"}`}>
                    {getAvatarLabel(animal)}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Display Name */}
          <div>
            <label className="font-mono text-[10px] text-muted-foreground uppercase tracking-wider block mb-1.5">
              What should we call you?
            </label>
            <input
              type="text"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              placeholder="e.g. Commander Nova"
              maxLength={40}
              className="w-full px-4 py-2.5 rounded-xl border border-glass-border bg-muted/20 font-mono text-sm text-foreground placeholder:text-muted-foreground outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/20 transition-all"
            />
          </div>

          {/* Role Selection */}
          <div>
            <label className="font-mono text-[10px] text-muted-foreground uppercase tracking-wider block mb-2">
              Your role
            </label>
            <div className="grid grid-cols-2 gap-2">
              {ROLES.map((r) => (
                <button
                  key={r.value}
                  type="button"
                  onClick={() => setRole(r.value)}
                  className={`flex items-center gap-2 px-3 py-2.5 rounded-xl font-mono text-xs transition-all border ${
                    role === r.value
                      ? "bg-primary/10 text-primary border-primary/30 shadow-sm"
                      : "border-glass-border text-muted-foreground hover:text-foreground hover:border-primary/20"
                  }`}
                >
                  <span>{r.icon}</span>
                  <span>{r.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Email (read-only) */}
          <div>
            <label className="font-mono text-[10px] text-muted-foreground uppercase tracking-wider block mb-1.5">
              Email
            </label>
            <input
              type="email"
              value={email}
              readOnly
              className="w-full px-4 py-2.5 rounded-xl border border-glass-border bg-muted/10 font-mono text-sm text-muted-foreground outline-none cursor-not-allowed"
            />
          </div>

          {/* Continue Button */}
          <button
            onClick={handleFinish}
            disabled={!isValid}
            className="w-full py-3 rounded-xl font-mono text-sm font-semibold transition-all disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            style={{
              background: isValid ? "var(--gradient-flow)" : undefined,
              color: isValid ? "hsl(var(--primary-foreground))" : undefined,
            }}
          >
            Let's Go <ChevronRight className="w-4 h-4" />
          </button>
        </div>

        <p className="font-mono text-[9px] text-muted-foreground text-center mt-4">
          You can change these later in Settings
        </p>
      </motion.div>
    </div>
  );
};

export default Onboarding;
