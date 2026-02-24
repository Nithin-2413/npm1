import { useState } from "react";
import { Link, useLocation, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { motion, AnimatePresence } from "framer-motion";
import {
  LayoutDashboard, Play, FileCode2, ClipboardList, FileText,
  Globe, Settings, User, ShoppingBag, Menu, X, Bell, Search,
  ChevronLeft
} from "lucide-react";

const NAV_ITEMS = [
  { label: "Dashboard", icon: LayoutDashboard, path: "/" },
  { label: "Execute", icon: Play, path: "/execute" },
  { label: "Blueprints", icon: FileCode2, path: "/blueprints" },
  { label: "Reports", icon: ClipboardList, path: "/reports" },
  { label: "Network", icon: Globe, path: "/network" },
  { label: "Settings", icon: Settings, path: "/settings" },
  { label: "Profile", icon: User, path: "/profile" },
];

const AppLayout = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [searchOpen, setSearchOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="min-h-screen bg-background flex w-full">
      {/* Background orbs */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden z-0">
        <div className="absolute top-[-20%] left-[-10%] w-[500px] h-[500px] rounded-full bg-glow-cyan/5 blur-[120px] animate-pulse-glow" />
        <div className="absolute top-[30%] right-[-10%] w-[600px] h-[600px] rounded-full bg-glow-purple/5 blur-[120px] animate-pulse-glow" style={{ animationDelay: "1s" }} />
        <div className="absolute bottom-[-10%] left-[30%] w-[400px] h-[400px] rounded-full bg-glow-pink/5 blur-[120px] animate-pulse-glow" style={{ animationDelay: "2s" }} />
      </div>

      {/* Sidebar */}
      <AnimatePresence mode="wait">
        {sidebarOpen && (
          <motion.aside
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: 240, opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed left-0 top-0 bottom-0 z-40 flex flex-col border-r border-glass-border overflow-hidden"
            style={{ background: "hsl(var(--glass-bg) / 0.85)", backdropFilter: "blur(40px)" }}
          >
            {/* Logo */}
            <div className="p-5 flex items-center gap-3 border-b border-glass-border">
              <span className="text-2xl animate-float">🌊</span>
              <div>
                <h1 className="text-lg font-black tracking-tight gradient-text">NPM</h1>
                <p className="font-mono text-[8px] text-muted-foreground tracking-widest uppercase">Neural Precision Monitor</p>
              </div>
              <button
                onClick={() => setSidebarOpen(false)}
                className="ml-auto text-muted-foreground hover:text-foreground transition-colors"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
            </div>

            {/* Nav */}
            <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
              {NAV_ITEMS.map((item) => {
                const isActive = location.pathname === item.path;
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`flex items-center gap-3 px-3 py-2.5 rounded-xl font-mono text-xs transition-all ${
                      isActive
                        ? "bg-primary/10 text-primary border border-primary/20 glass-glow-cyan"
                        : "text-muted-foreground hover:text-foreground hover:bg-muted/20 border border-transparent"
                    }`}
                  >
                    <item.icon className="w-4 h-4 shrink-0" />
                    <span>{item.label}</span>
                  </Link>
                );
              })}
            </nav>

            {/* Status & Logout */}
            <div className="p-4 border-t border-glass-border space-y-3">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-primary animate-pulse" />
                <span className="font-mono text-[10px] text-primary">System Online</span>
              </div>
              {user && (
                <div className="flex items-center justify-between">
                  <span className="font-mono text-[10px] text-muted-foreground truncate">{user.email}</span>
                  <button
                    onClick={handleLogout}
                    className="font-mono text-[10px] text-destructive hover:text-destructive/80 transition-colors"
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
      <div className={`flex-1 flex flex-col transition-all duration-200 relative z-10 ${sidebarOpen ? "ml-[240px]" : "ml-0"}`}>
        {/* Top header */}
        <header className="sticky top-0 z-30 border-b border-glass-border px-4 py-3 flex items-center gap-3"
          style={{ background: "hsl(var(--glass-bg) / 0.7)", backdropFilter: "blur(20px)" }}
        >
          {!sidebarOpen && (
            <button
              onClick={() => setSidebarOpen(true)}
              className="text-muted-foreground hover:text-foreground transition-colors p-1.5 rounded-lg hover:bg-muted/20"
            >
              <Menu className="w-4 h-4" />
            </button>
          )}

          {/* Search */}
          <div className="flex-1 max-w-md">
            <div className="glass-panel-strong flex items-center gap-2 px-3 py-1.5 rounded-xl">
              <Search className="w-3.5 h-3.5 text-muted-foreground" />
              <input
                placeholder="Search blueprints, reports, executions... (⌘K)"
                className="flex-1 bg-transparent font-mono text-xs text-foreground placeholder:text-muted-foreground outline-none"
              />
              <kbd className="font-mono text-[9px] px-1.5 py-0.5 rounded border border-glass-border text-muted-foreground">⌘K</kbd>
            </div>
          </div>

          <div className="flex items-center gap-2 ml-auto">
            {/* Notifications */}
            <button className="relative p-2 rounded-xl text-muted-foreground hover:text-foreground hover:bg-muted/20 transition-colors">
              <Bell className="w-4 h-4" />
              <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-accent" />
            </button>

            {/* Profile */}
            <div className="flex items-center gap-2 pl-2 border-l border-glass-border">
              <div className="w-7 h-7 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center text-[10px] font-bold text-primary-foreground">
                {user?.name?.slice(0, 2).toUpperCase() || "U"}
              </div>
              <span className="font-mono text-xs text-muted-foreground hidden sm:inline">{user?.name || "user"}</span>
            </div>
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
