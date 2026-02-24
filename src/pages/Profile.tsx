import { useState, useEffect } from "react";
import { GlassPanel } from "@/components/GlassPanel";
import { Save, Copy, Trash2, Plus, Eye, EyeOff } from "lucide-react";
import { AnimatedAvatar, AVATAR_ANIMALS, AvatarAnimal, getAvatarLabel } from "@/components/AnimatedAvatar";

const Profile = () => {
  const [name, setName] = useState(() => localStorage.getItem("npm_display_name") || "QA Admin");
  const [email] = useState("qa_admin@npmmonitor.dev");
  const [bio, setBio] = useState(() => localStorage.getItem("npm_bio") || "Senior QA Engineer. Automating everything through liquid glass.");
  const [showKey, setShowKey] = useState(false);
  const [selectedAvatar, setSelectedAvatar] = useState<AvatarAnimal>(() => {
    return (localStorage.getItem("npm_avatar") as AvatarAnimal) || "lion";
  });

  useEffect(() => {
    localStorage.setItem("npm_avatar", selectedAvatar);
    window.dispatchEvent(new CustomEvent("avatar-changed", { detail: selectedAvatar }));
  }, [selectedAvatar]);

  const [apiKeys, setApiKeys] = useState([
    { id: "key_1", name: "Production", key: "npm_sk_prod_" + crypto.randomUUID().slice(0, 16), created: "2026-01-15", lastUsed: "2m ago", visible: false },
    { id: "key_2", name: "Development", key: "npm_sk_dev_" + crypto.randomUUID().slice(0, 16), created: "2026-02-01", lastUsed: "1h ago", visible: false },
  ]);

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
              <label className="font-mono text-[10px] text-muted-foreground uppercase tracking-wider block mb-1">Name</label>
              <input value={name} onChange={(e) => setName(e.target.value)} className="w-full bg-muted/20 border border-glass-border rounded-xl px-3 py-2 font-mono text-base text-foreground outline-none focus:ring-1 focus:ring-primary/40" />
            </div>
            <div>
              <label className="font-mono text-[10px] text-muted-foreground uppercase tracking-wider block mb-1">Email</label>
              <input value={email} readOnly className="w-full bg-muted/10 border border-glass-border rounded-xl px-3 py-2 font-mono text-sm text-muted-foreground outline-none cursor-not-allowed" />
            </div>
            <div>
              <label className="font-mono text-[10px] text-muted-foreground uppercase tracking-wider block mb-1">Bio</label>
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

      {/* API Keys */}
      <GlassPanel title="API Keys" icon="🔑" glow="none">
        <div className="space-y-3">
          {apiKeys.map((apiKey) => (
            <div key={apiKey.id} className="glass-panel-strong p-4 flex items-center justify-between rounded-lg">
              <div>
                <span className="font-mono text-xs font-semibold text-foreground">{apiKey.name}</span>
                <div className="flex items-center gap-2 mt-1">
                  <span className="font-mono text-[11px] text-muted-foreground">
                    {apiKey.visible ? apiKey.key : apiKey.key.slice(0, 11) + "••••••••"}
                  </span>
                  <button
                    onClick={() => setApiKeys(keys => keys.map(k => k.id === apiKey.id ? { ...k, visible: !k.visible } : k))}
                    className="text-muted-foreground hover:text-foreground transition-colors"
                  >
                    {apiKey.visible ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
                  </button>
                  <button
                    onClick={() => navigator.clipboard.writeText(apiKey.key)}
                    className="text-muted-foreground hover:text-foreground transition-colors"
                  >
                    <Copy className="w-3 h-3" />
                  </button>
                </div>
                <span className="font-mono text-[9px] text-muted-foreground">Created: {apiKey.created} • Last used: {apiKey.lastUsed}</span>
              </div>
              <button
                onClick={() => setApiKeys(keys => keys.filter(k => k.id !== apiKey.id))}
                className="p-2 rounded-lg border border-destructive/30 text-destructive hover:bg-destructive/10 transition-colors"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          ))}
          <button
            onClick={() => {
              const newKey = {
                id: crypto.randomUUID(),
                name: `Key ${apiKeys.length + 1}`,
                key: "npm_sk_" + crypto.randomUUID().replace(/-/g, "").slice(0, 24),
                created: new Date().toISOString().split("T")[0],
                lastUsed: "just now",
                visible: true,
              };
              setApiKeys(keys => [...keys, newKey]);
            }}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl font-mono text-xs border border-dashed border-glass-border text-muted-foreground hover:text-primary hover:border-primary/30 transition-colors"
          >
            <Plus className="w-3.5 h-3.5" /> Generate New API Key
          </button>
        </div>
      </GlassPanel>
    </div>
  );
};

export default Profile;
