import { useState, useEffect } from "react";
import { GlassPanel } from "@/components/GlassPanel";
import { Save, Trash2, Plus, Eye, EyeOff, ChevronDown, ChevronUp, X } from "lucide-react";
import { AnimatedAvatar, AVATAR_ANIMALS, AvatarAnimal, getAvatarLabel } from "@/components/AnimatedAvatar";
import { motion, AnimatePresence } from "framer-motion";

interface Secret {
  id: string;
  testEnv: string;
  releaseBranch: string;
  url: string;
  username: string;
  password: string;
  createdAt: string;
}

const Profile = () => {
  const [name, setName] = useState(() => localStorage.getItem("npm_display_name") || "QA Admin");
  const [email] = useState("qa_admin@npmmonitor.dev");
  const [bio, setBio] = useState(() => localStorage.getItem("npm_bio") || "Senior QA Engineer. Automating everything through liquid glass.");
  const [selectedAvatar, setSelectedAvatar] = useState<AvatarAnimal>(() => {
    return (localStorage.getItem("npm_avatar") as AvatarAnimal) || "lion";
  });

  useEffect(() => {
    localStorage.setItem("npm_avatar", selectedAvatar);
    window.dispatchEvent(new CustomEvent("avatar-changed", { detail: selectedAvatar }));
  }, [selectedAvatar]);

  const [secrets, setSecrets] = useState<Secret[]>(() => {
    try {
      const stored = localStorage.getItem("npm_secrets");
      return stored ? JSON.parse(stored) : [];
    } catch { return []; }
  });
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [visiblePasswords, setVisiblePasswords] = useState<Set<string>>(new Set());
  const [showAddForm, setShowAddForm] = useState(false);
  const [newSecret, setNewSecret] = useState({ testEnv: "", releaseBranch: "", url: "", username: "", password: "" });

  useEffect(() => {
    localStorage.setItem("npm_secrets", JSON.stringify(secrets));
  }, [secrets]);

  const togglePasswordVisibility = (id: string) => {
    setVisiblePasswords(prev => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const handleAddSecret = () => {
    if (!newSecret.testEnv.trim() || !newSecret.url.trim()) return;
    const secret: Secret = {
      id: crypto.randomUUID(),
      ...newSecret,
      createdAt: new Date().toISOString().split("T")[0],
    };
    setSecrets(prev => [...prev, secret]);
    setNewSecret({ testEnv: "", releaseBranch: "", url: "", username: "", password: "" });
    setShowAddForm(false);
    setExpandedId(secret.id);
  };

  const inputClass = "w-full bg-muted/20 border border-glass-border rounded-xl px-3 py-2 font-mono text-xs text-foreground outline-none focus:ring-1 focus:ring-primary/40 placeholder:text-muted-foreground/50";
  const labelClass = "font-mono text-[10px] text-muted-foreground uppercase tracking-wider block mb-1";

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-black tracking-tight gradient-text flex items-center gap-2">
          <span>👤</span> Profile
        </h1>
        <p className="font-mono text-xs text-muted-foreground mt-1">Account management</p>
      </div>

      {/* Avatar Selection */}
      <GlassPanel title="Choose Avatar" icon="✨" glow="purple">
        <div className="flex flex-wrap items-center gap-4">
          {AVATAR_ANIMALS.map((animal) => (
            <div key={animal} className="flex flex-col items-center gap-1.5">
              <AnimatedAvatar
                animal={animal}
                size="md"
                selected={selectedAvatar === animal}
                onClick={() => setSelectedAvatar(animal)}
              />
              <span className={`font-mono text-[9px] ${selectedAvatar === animal ? "text-primary font-semibold" : "text-muted-foreground"}`}>
                {getAvatarLabel(animal)}
              </span>
            </div>
          ))}
        </div>
      </GlassPanel>

      {/* Profile Card */}
      <GlassPanel glow="cyan">
        <div className="flex items-start gap-6">
          <AnimatedAvatar animal={selectedAvatar} size="lg" />
          <div className="flex-1 space-y-3">
            <div>
              <label className={labelClass}>Name</label>
              <input value={name} onChange={(e) => setName(e.target.value)} className="w-full bg-muted/20 border border-glass-border rounded-xl px-3 py-2 font-mono text-base text-foreground outline-none focus:ring-1 focus:ring-primary/40" />
            </div>
            <div>
              <label className={labelClass}>Email</label>
              <input value={email} readOnly className="w-full bg-muted/10 border border-glass-border rounded-xl px-3 py-2 font-mono text-sm text-muted-foreground outline-none cursor-not-allowed" />
            </div>
            <div>
              <label className={labelClass}>Bio</label>
              <textarea value={bio} onChange={(e) => setBio(e.target.value)} rows={2} className="w-full bg-muted/20 border border-glass-border rounded-xl px-3 py-2 font-mono text-xs text-foreground outline-none focus:ring-1 focus:ring-primary/40 resize-none" />
            </div>
            <button
              onClick={() => {
                localStorage.setItem("npm_display_name", name);
                localStorage.setItem("npm_bio", bio);
                window.dispatchEvent(new CustomEvent("profile-updated", { detail: { name, bio } }));
              }}
              className="flex items-center gap-1.5 px-4 py-2 rounded-xl font-mono text-xs bg-primary/10 text-primary border border-primary/30 hover:bg-primary/20 transition-colors"
            >
              <Save className="w-3 h-3" /> Save Changes
            </button>
          </div>
        </div>
      </GlassPanel>

      {/* Member Since */}
      <GlassPanel title="Member Since" icon="📅" glow="purple">
        <p className="font-mono text-sm text-muted-foreground">January 2026</p>
      </GlassPanel>

      {/* Secrets */}
      <GlassPanel title="Secrets" icon="🔐" glow="none">
        <div className="space-y-3">
          {secrets.map((secret) => {
            const isExpanded = expandedId === secret.id;
            const pwVisible = visiblePasswords.has(secret.id);
            return (
              <div key={secret.id} className="glass-panel-strong rounded-xl overflow-hidden">
                <button
                  onClick={() => setExpandedId(isExpanded ? null : secret.id)}
                  className="w-full flex items-center justify-between p-4 text-left"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-semibold text-foreground truncate">{secret.testEnv}</span>
                      {secret.releaseBranch && (
                        <span className="font-mono text-[9px] px-2 py-0.5 rounded-full bg-primary/10 text-primary border border-primary/20 shrink-0">
                          {secret.releaseBranch}
                        </span>
                      )}
                    </div>
                    <span className="font-mono text-[10px] text-muted-foreground mt-0.5 block truncate">{secret.url}</span>
                  </div>
                  <div className="flex items-center gap-2 ml-3">
                    <span className="font-mono text-[9px] text-muted-foreground shrink-0">{secret.createdAt}</span>
                    {isExpanded ? <ChevronUp className="w-3.5 h-3.5 text-muted-foreground" /> : <ChevronDown className="w-3.5 h-3.5 text-muted-foreground" />}
                  </div>
                </button>

                <AnimatePresence>
                  {isExpanded && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.2 }}
                      className="overflow-hidden"
                    >
                      <div className="px-4 pb-4 space-y-2.5 border-t border-glass-border pt-3">
                        <div>
                          <label className={labelClass}>URL</label>
                          <p className="font-mono text-xs text-foreground break-all">{secret.url}</p>
                        </div>
                        <div>
                          <label className={labelClass}>Username</label>
                          <p className="font-mono text-xs text-foreground">{secret.username || "—"}</p>
                        </div>
                        <div>
                          <label className={labelClass}>Password</label>
                          <div className="flex items-center gap-2">
                            <p className="font-mono text-xs text-foreground">
                              {pwVisible ? secret.password : "••••••••••"}
                            </p>
                            <button onClick={() => togglePasswordVisibility(secret.id)} className="text-muted-foreground hover:text-foreground transition-colors">
                              {pwVisible ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
                            </button>
                          </div>
                        </div>
                        <div className="flex justify-end pt-1">
                          <button
                            onClick={() => setSecrets(s => s.filter(x => x.id !== secret.id))}
                            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-mono text-[10px] border border-destructive/30 text-destructive hover:bg-destructive/10 transition-colors"
                          >
                            <Trash2 className="w-3 h-3" /> Remove
                          </button>
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            );
          })}

          {/* Add New Secret Form */}
          <AnimatePresence>
            {showAddForm && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="overflow-hidden"
              >
                <div className="glass-panel-strong rounded-xl p-4 space-y-3">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-mono text-xs font-semibold text-foreground">New Secret</span>
                    <button onClick={() => setShowAddForm(false)} className="text-muted-foreground hover:text-foreground transition-colors">
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className={labelClass}>Test Environment *</label>
                      <input
                        value={newSecret.testEnv}
                        onChange={(e) => setNewSecret(s => ({ ...s, testEnv: e.target.value }))}
                        placeholder="e.g. Staging, QA, UAT"
                        className={inputClass}
                      />
                    </div>
                    <div>
                      <label className={labelClass}>Release Branch</label>
                      <input
                        value={newSecret.releaseBranch}
                        onChange={(e) => setNewSecret(s => ({ ...s, releaseBranch: e.target.value }))}
                        placeholder="e.g. release/2.4"
                        className={inputClass}
                      />
                    </div>
                  </div>
                  <div>
                    <label className={labelClass}>URL *</label>
                    <input
                      value={newSecret.url}
                      onChange={(e) => setNewSecret(s => ({ ...s, url: e.target.value }))}
                      placeholder="https://staging.example.com"
                      className={inputClass}
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className={labelClass}>Username</label>
                      <input
                        value={newSecret.username}
                        onChange={(e) => setNewSecret(s => ({ ...s, username: e.target.value }))}
                        placeholder="qa_user"
                        className={inputClass}
                      />
                    </div>
                    <div>
                      <label className={labelClass}>Password</label>
                      <input
                        type="password"
                        value={newSecret.password}
                        onChange={(e) => setNewSecret(s => ({ ...s, password: e.target.value }))}
                        placeholder="••••••••"
                        className={inputClass}
                      />
                    </div>
                  </div>
                  <button
                    onClick={handleAddSecret}
                    disabled={!newSecret.testEnv.trim() || !newSecret.url.trim()}
                    className="w-full py-2.5 rounded-xl font-mono text-xs font-semibold bg-foreground text-background hover:opacity-90 active:scale-[0.98] transition-all disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    Save Secret
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {!showAddForm && (
            <button
              onClick={() => setShowAddForm(true)}
              className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl font-mono text-xs border border-dashed border-glass-border text-muted-foreground hover:text-primary hover:border-primary/30 transition-colors"
            >
              <Plus className="w-3.5 h-3.5" /> Add Secret
            </button>
          )}
        </div>
      </GlassPanel>
    </div>
  );
};

export default Profile;
