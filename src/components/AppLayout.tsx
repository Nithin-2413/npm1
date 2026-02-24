import { useState, useEffect } from "react";
import { Link, useLocation, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { motion, AnimatePresence } from "framer-motion";
import { NotificationPanel } from "@/components/NotificationPanel";
import { GlobalSearchModal } from "@/components/GlobalSearchModal";
import { KeyboardShortcutsModal } from "@/components/KeyboardShortcutsModal";
import { SystemPulse } from "@/components/SystemPulse";
import { AnimatedAvatar, AvatarAnimal, getAvatarEmoji } from "@/components/AnimatedAvatar";
import {
  LayoutDashboard, Play, FileCode2, ClipboardList,
  Settings, Menu, Search,
  ChevronLeft, Keyboard
} from "lucide-react";

const NAV_ITEMS = [
  { label: "Dashboard", icon: LayoutDashboard, path: "/", shortcut: "G D", color: "theme-blue" },
  { label: "Execute", icon: Play, path: "/execute", shortcut: "G E", color: "theme-green" },
  { label: "Blueprints", icon: FileCode2, path: "/blueprints", shortcut: "G B", color: "theme-violet" },
  { label: "Reports", icon: ClipboardList, path: "/reports", shortcut: "G R", color: "theme-orange" },
  { label: "Settings", icon: Settings, path: "/settings", shortcut: "G S", color: "theme-pistachio" },
];

const NAV_COLOR_CLASSES: Record<string, { bg: string; text: string; border: string; glow: string }> = {
  "theme-blue":      { bg: "bg-theme-blue/10",      text: "text-theme-blue",      border: "border-theme-blue/20",      glow: "" },
  "theme-green":     { bg: "bg-theme-green/10",     text: "text-theme-green",     border: "border-theme-green/20",     glow: "" },
  "theme-violet":    { bg: "bg-theme-violet/10",    text: "text-theme-violet",    border: "border-theme-violet/20",    glow: "" },
  "theme-orange":    { bg: "bg-theme-orange/10",    text: "text-theme-orange",    border: "border-theme-orange/20",    glow: "" },
  "theme-pink":      { bg: "bg-theme-pink/10",      text: "text-theme-pink",      border: "border-theme-pink/20",      glow: "" },
  "theme-pistachio": { bg: "bg-theme-pistachio/10", text: "text-theme-pistachio", border: "border-theme-pistachio/20", glow: "" },
  "theme-blueberry": { bg: "bg-theme-blueberry/10", text: "text-theme-blueberry", border: "border-theme-blueberry/20", glow: "" },
};

const AppLayout = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [avatar, setAvatar] = useState<AvatarAnimal>(() => {
    return (localStorage.getItem("npm_avatar") as AvatarAnimal) || "lion";
  });

  // Listen for avatar changes from Profile page
  useEffect(() => {
    const handler = (e: Event) => setAvatar((e as CustomEvent).detail);
    window.addEventListener("avatar-changed", handler);
    return () => window.removeEventListener("avatar-changed", handler);
  }, []);

  // Keyboard navigation shortcuts (G + key)
  useEffect(() => {
    let gPressed = false;
    let gTimeout: ReturnType<typeof setTimeout>;

    const handler = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;

      if (e.key === "g" && !e.metaKey && !e.ctrlKey) {
        gPressed = true;
        clearTimeout(gTimeout);
        gTimeout = setTimeout(() => { gPressed = false; }, 500);
        return;
      }

      if (gPressed) {
        gPressed = false;
        const map: Record<string, string> = { d: "/", e: "/execute", b: "/blueprints", r: "/reports", s: "/settings" };
        if (map[e.key]) {
          e.preventDefault();
          navigate(map[e.key]);
        }
      }
    };
    window.addEventListener("keydown", handler);
    return () => { window.removeEventListener("keydown", handler); clearTimeout(gTimeout); };
  }, [navigate]);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="min-h-screen bg-background flex w-full">
      {/* Global modals */}
      <GlobalSearchModal />
      <KeyboardShortcutsModal />

      {/* Soft ambient background — subtle, not distracting */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden z-0">
        <div className="absolute top-[-20%] left-[-10%] w-[600px] h-[600px] rounded-full bg-glow-cyan/3 blur-[150px] animate-pulse-glow" />
        <div className="absolute top-[40%] right-[-10%] w-[500px] h-[500px] rounded-full bg-glow-purple/3 blur-[150px] animate-pulse-glow" style={{ animationDelay: "2s" }} />
        <div className="absolute bottom-[-15%] left-[25%] w-[450px] h-[450px] rounded-full bg-glow-pink/3 blur-[150px] animate-pulse-glow" style={{ animationDelay: "4s" }} />
      </div>

      {/* Sidebar — macOS Finder style */}
      <AnimatePresence mode="wait">
        {sidebarOpen && (
          <motion.aside
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: 240, opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            transition={{ duration: 0.25, ease: [0.25, 0.1, 0.25, 1] }}
            className="fixed left-0 top-0 bottom-0 z-40 flex flex-col border-r overflow-hidden"
            style={{
              borderColor: "hsl(var(--glass-border) / 0.2)",
              background: "hsl(var(--glass-bg) / 0.25)",
              backdropFilter: "blur(60px) saturate(1.6)",
              WebkitBackdropFilter: "blur(60px) saturate(1.6)",
              boxShadow: "inset 1px 0 0 0 hsl(var(--glass-border) / 0.15), inset -1px 0 0 0 hsl(var(--glass-border) / 0.08), 4px 0 24px -4px hsl(var(--glass-bg) / 0.1)",
            }}
          >
            {/* Logo */}
            <div className="p-5 flex items-center justify-center gap-3 border-b" style={{ borderColor: "hsl(var(--glass-border) / 0.3)" }}>
              <span className="text-2xl animate-float">🌊</span>
              <div className="text-center">
                <h1 className="text-xl font-black tracking-tight bg-clip-text text-transparent" style={{ fontFamily: "'Sen', sans-serif", backgroundImage: "linear-gradient(135deg, #7a5c12, #b8942e, #e2c56d, #f5e2a0, #e2c56d, #b8942e, #7a5c12)", backgroundSize: "300% auto", animation: "gold-shine 4s linear infinite" }}>NPM</h1>
                <p className="text-[8px] text-muted-foreground tracking-widest uppercase" style={{ fontFamily: "'Sen', sans-serif" }}>Neural Precision Monitor</p>
              </div>
              <button
                onClick={() => setSidebarOpen(false)}
                className="ml-auto text-muted-foreground hover:text-foreground transition-colors"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
            </div>

            {/* Nav */}
            <nav className="flex-1 p-3 space-y-1">
              {NAV_ITEMS.map((item) => {
                const isActive = location.pathname === item.path;
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`flex items-center gap-3 px-3 py-2 rounded-[10px] text-[12px] tracking-tight transition-all duration-200 group ${
                      isActive
                        ? `${NAV_COLOR_CLASSES[item.color].text} ${NAV_COLOR_CLASSES[item.color].border} border font-medium`
                        : "text-muted-foreground hover:text-foreground hover:bg-muted/15 border border-transparent"
                    }`}
                    style={isActive ? {
                      background: `hsl(var(--glass-bg) / 0.6)`,
                      backdropFilter: "blur(12px)",
                      boxShadow: "0 1px 3px -1px hsl(var(--background) / 0.3), inset 0 0.5px 0 0 hsl(var(--foreground) / 0.04)"
                    } : undefined}
                  >
                    <item.icon className="w-4 h-4 shrink-0" strokeWidth={isActive ? 2 : 1.5} />
                    <span className="flex-1" style={{ fontFamily: "'Sen', sans-serif" }}>{item.label}</span>
                    {item.shortcut && (
                      <span className="font-mono text-[8px] text-muted-foreground/40 group-hover:text-muted-foreground transition-colors">
                        {item.shortcut}
                      </span>
                    )}
                  </Link>
                );
              })}
            </nav>

            {/* System Pulse */}
            <div className="px-4 py-3 border-t" style={{ borderColor: "hsl(var(--glass-border) / 0.3)" }}>
              <SystemPulse />
            </div>

            {/* User & Logout */}
            <div className="p-4 border-t space-y-3" style={{ borderColor: "hsl(var(--glass-border) / 0.3)" }}>
              {user && (
                <div className="flex items-center gap-2">
                  <AnimatedAvatar animal={avatar} size="sm" />
                  <span className="font-mono text-[10px] text-muted-foreground truncate flex-1">{user.email}</span>
                  <button
                    onClick={handleLogout}
                    className="font-mono text-[10px] text-destructive hover:text-destructive/80 transition-colors shrink-0"
                  >
                    Logout
                  </button>
                </div>
              )}
              <p className="font-mono text-[9px] text-muted-foreground">v2.4.1 • Liquid Engine</p>
            </div>
          </motion.aside>
        )}
      </AnimatePresence>

      {/* Main content */}
      <div className={`flex-1 flex flex-col transition-all duration-300 ease-[cubic-bezier(0.25,0.1,0.25,1)] relative z-10 ${sidebarOpen ? "ml-[240px]" : "ml-0"}`}>
        {/* Top header — macOS toolbar style */}
        <header className="sticky top-0 z-30 border-b px-5 py-2.5 flex items-center gap-3"
          style={{
            borderColor: "hsl(var(--glass-border) / 0.2)",
            background: "hsl(var(--glass-bg) / 0.3)",
            backdropFilter: "blur(50px) saturate(2)",
            WebkitBackdropFilter: "blur(50px) saturate(2)",
          }}
        >
          {!sidebarOpen && (
            <button
              onClick={() => setSidebarOpen(true)}
              className="text-muted-foreground hover:text-foreground transition-colors p-1.5 rounded-lg hover:bg-muted/20"
            >
              <Menu className="w-4 h-4" />
            </button>
          )}

          {/* Search — now opens modal */}
          <div className="flex-1 max-w-xs mx-auto">
            <button
              onClick={() => {
                window.dispatchEvent(new CustomEvent("open-search"));
              }}
              className="w-full glass-panel-strong flex items-center gap-2 px-3 py-1.5 rounded-xl text-left group hover:ring-1 hover:ring-primary/20 transition-all"
            >
              <Search className="w-3.5 h-3.5 text-muted-foreground" />
              <span className="flex-1 font-mono text-xs text-muted-foreground group-hover:text-foreground/60 transition-colors">
                Search everything...
              </span>
              <kbd className="font-mono text-[9px] px-1.5 py-0.5 rounded border border-glass-border text-muted-foreground">⌘K</kbd>
            </button>
          </div>

          <div className="flex items-center gap-1 ml-auto">
            {/* Keyboard shortcuts hint */}
            <button
              onClick={() => window.dispatchEvent(new KeyboardEvent("keydown", { key: "?" }))}
              className="p-2 rounded-xl text-muted-foreground hover:text-foreground hover:bg-muted/20 transition-colors"
              title="Keyboard shortcuts"
            >
              <Keyboard className="w-4 h-4" />
            </button>

            {/* Notifications */}
            <NotificationPanel />

            {/* Profile */}
            <Link to="/profile" className="flex items-center gap-2 pl-2 ml-1 border-l border-glass-border hover:opacity-80 transition-opacity">
              <AnimatedAvatar animal={avatar} size="sm" />
              <span className="font-mono text-xs text-muted-foreground hidden sm:inline">{user?.name || "user"}</span>
            </Link>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 p-6 overflow-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default AppLayout;
