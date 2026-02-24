import { useState } from "react";
import { GlassPanel } from "@/components/GlassPanel";
import {
  Monitor, Globe, Wifi, Brain, FileCode2, ClipboardList,
  Zap, Database, ChevronRight, Save, RotateCcw, Trash2,
  TestTube, Key
} from "lucide-react";

interface SettingsSection {
  id: string;
  label: string;
  icon: React.ReactNode;
}

const SECTIONS: SettingsSection[] = [
  { id: "general", label: "General", icon: <Monitor className="w-4 h-4" /> },
  { id: "browser", label: "Browser", icon: <Globe className="w-4 h-4" /> },
  { id: "network", label: "Network", icon: <Wifi className="w-4 h-4" /> },
  { id: "ai", label: "AI & LLM", icon: <Brain className="w-4 h-4" /> },
  { id: "blueprints", label: "Blueprints", icon: <FileCode2 className="w-4 h-4" /> },
  { id: "reports", label: "Reports", icon: <ClipboardList className="w-4 h-4" /> },
  { id: "integrations", label: "Integrations", icon: <Zap className="w-4 h-4" /> },
  { id: "advanced", label: "Advanced", icon: <Database className="w-4 h-4" /> },
];

const Toggle = ({ checked, onChange, label }: { checked: boolean; onChange: () => void; label: string }) => (
  <label className="flex items-center justify-between cursor-pointer group">
    <span className="font-mono text-xs text-muted-foreground group-hover:text-foreground transition-colors">{label}</span>
    <div onClick={onChange} className={`w-9 h-5 rounded-full flex items-center transition-colors cursor-pointer ${checked ? "bg-primary/40" : "bg-muted/40"}`}>
      <div className={`w-4 h-4 rounded-full bg-foreground transition-transform ${checked ? "translate-x-4.5" : "translate-x-0.5"}`} style={{ transform: checked ? "translateX(18px)" : "translateX(2px)" }} />
    </div>
  </label>
);

const Slider = ({ value, onChange, min, max, label, unit }: { value: number; onChange: (v: number) => void; min: number; max: number; label: string; unit: string }) => (
  <div className="space-y-1">
    <div className="flex items-center justify-between">
      <span className="font-mono text-xs text-muted-foreground">{label}</span>
      <span className="font-mono text-xs text-primary">{value}{unit}</span>
    </div>
    <input type="range" min={min} max={max} value={value} onChange={(e) => onChange(parseInt(e.target.value))} className="w-full h-1 bg-muted/40 rounded-full appearance-none accent-primary" />
  </div>
);

const Settings = () => {
  const [activeSection, setActiveSection] = useState("general");

  // General
  const [theme, setTheme] = useState("dark");
  const [glassIntensity, setGlassIntensity] = useState(75);
  const [notifications, setNotifications] = useState(true);
  const [emailNotifs, setEmailNotifs] = useState(false);

  // Browser
  const [browser, setBrowser] = useState("chromium");
  const [headless, setHeadless] = useState(true);
  const [defaultTimeout, setDefaultTimeout] = useState(15);
  const [slowMotion, setSlowMotion] = useState(0);
  const [autoScreenshot, setAutoScreenshot] = useState(true);
  const [videoRecording, setVideoRecording] = useState(false);

  // Network
  const [interceptAll, setInterceptAll] = useState(true);
  const [captureHeaders, setCaptureHeaders] = useState(true);
  const [captureBodies, setCaptureBodies] = useState(true);
  const [logConsole, setLogConsole] = useState(true);

  // AI
  const [aiProvider, setAiProvider] = useState("groq");
  const [aiModel, setAiModel] = useState("qwen2.5-coder-32b");
  const [temperature, setTemperature] = useState(30);
  const [streaming, setStreaming] = useState(true);
  const [autoAnalyze, setAutoAnalyze] = useState(true);

  // Blueprints
  const [autoSave, setAutoSave] = useState(true);
  const [validateSelectors, setValidateSelectors] = useState(true);

  // Reports
  const [reportFormat, setReportFormat] = useState("json");
  const [autoExport, setAutoExport] = useState(false);
  const [retentionDays, setRetentionDays] = useState(30);
  const [includeScreenshots, setIncludeScreenshots] = useState(true);
  const [includeNetwork, setIncludeNetwork] = useState(true);
  const [includeConsole, setIncludeConsole] = useState(true);

  // Advanced
  const [parallelExec, setParallelExec] = useState(3);
  const [maxRetries, setMaxRetries] = useState(2);
  const [debugMode, setDebugMode] = useState(false);

  const renderSection = () => {
    switch (activeSection) {
      case "general":
        return (
          <div className="space-y-6">
            <div>
              <h3 className="font-mono text-sm font-semibold text-foreground mb-4">Theme</h3>
              <div className="flex gap-2">
                {["dark", "light", "auto"].map(t => (
                  <button key={t} onClick={() => setTheme(t)}
                    className={`font-mono text-xs px-4 py-2 rounded-xl border transition-all capitalize ${
                      theme === t ? "border-primary/40 bg-primary/10 text-primary" : "border-glass-border text-muted-foreground hover:text-foreground"
                    }`}
                  >{t}</button>
                ))}
              </div>
              <div className="mt-4">
                <Slider value={glassIntensity} onChange={setGlassIntensity} min={0} max={100} label="Glassmorphism Intensity" unit="%" />
              </div>
            </div>
            <div className="border-t border-glass-border pt-4 space-y-3">
              <h3 className="font-mono text-sm font-semibold text-foreground mb-2">Notifications</h3>
              <Toggle checked={notifications} onChange={() => setNotifications(!notifications)} label="Enable Notifications" />
              <Toggle checked={emailNotifs} onChange={() => setEmailNotifs(!emailNotifs)} label="Email Notifications" />
            </div>
          </div>
        );
      case "browser":
        return (
          <div className="space-y-6">
            <div>
              <h3 className="font-mono text-sm font-semibold text-foreground mb-4">Browser Engine</h3>
              <div className="flex gap-2">
                {["chromium", "firefox", "webkit"].map(b => (
                  <button key={b} onClick={() => setBrowser(b)}
                    className={`font-mono text-xs px-4 py-2 rounded-xl border transition-all capitalize ${
                      browser === b ? "border-primary/40 bg-primary/10 text-primary" : "border-glass-border text-muted-foreground hover:text-foreground"
                    }`}
                  >{b}</button>
                ))}
              </div>
            </div>
            <div className="space-y-3">
              <Toggle checked={headless} onChange={() => setHeadless(!headless)} label="Headless Mode" />
              <Slider value={defaultTimeout} onChange={setDefaultTimeout} min={5} max={60} label="Default Timeout" unit="s" />
              <Slider value={slowMotion} onChange={setSlowMotion} min={0} max={5000} label="Slow Motion Delay" unit="ms" />
            </div>
            <div className="border-t border-glass-border pt-4 space-y-3">
              <h3 className="font-mono text-sm font-semibold text-foreground mb-2">Screenshots & Video</h3>
              <Toggle checked={autoScreenshot} onChange={() => setAutoScreenshot(!autoScreenshot)} label="Auto-screenshot on Error" />
              <Toggle checked={videoRecording} onChange={() => setVideoRecording(!videoRecording)} label="Video Recording" />
            </div>
          </div>
        );
      case "network":
        return (
          <div className="space-y-3">
            <Toggle checked={interceptAll} onChange={() => setInterceptAll(!interceptAll)} label="Intercept All Requests" />
            <Toggle checked={logConsole} onChange={() => setLogConsole(!logConsole)} label="Log Console Messages" />
            <Toggle checked={captureHeaders} onChange={() => setCaptureHeaders(!captureHeaders)} label="Capture Headers" />
            <Toggle checked={captureBodies} onChange={() => setCaptureBodies(!captureBodies)} label="Capture Bodies" />
          </div>
        );
      case "ai":
        return (
          <div className="space-y-6">
            <div>
              <h3 className="font-mono text-sm font-semibold text-foreground mb-4">Provider</h3>
              <div className="flex gap-2">
                {["groq", "openai", "anthropic"].map(p => (
                  <button key={p} onClick={() => setAiProvider(p)}
                    className={`font-mono text-xs px-4 py-2 rounded-xl border transition-all capitalize ${
                      aiProvider === p ? "border-primary/40 bg-primary/10 text-primary" : "border-glass-border text-muted-foreground hover:text-foreground"
                    }`}
                  >{p}</button>
                ))}
              </div>
            </div>
            <div className="space-y-3">
              <div>
                <span className="font-mono text-xs text-muted-foreground block mb-1">API Key</span>
                <div className="flex gap-2">
                  <input type="password" value="gsk_••••••••••••••••" readOnly className="flex-1 bg-muted/20 border border-glass-border rounded-xl px-3 py-2 font-mono text-xs text-foreground outline-none" />
                  <button className="px-3 py-2 rounded-xl font-mono text-[10px] border border-primary/30 text-primary hover:bg-primary/10 transition-colors flex items-center gap-1">
                    <TestTube className="w-3 h-3" /> Test
                  </button>
                </div>
              </div>
              <div>
                <span className="font-mono text-xs text-muted-foreground block mb-1">Model</span>
                <select value={aiModel} onChange={(e) => setAiModel(e.target.value)} className="w-full bg-muted/20 border border-glass-border rounded-xl px-3 py-2 font-mono text-xs text-foreground outline-none cursor-pointer">
                  <option className="bg-background" value="qwen2.5-coder-32b">qwen2.5-coder-32b-instruct</option>
                  <option className="bg-background" value="llama-3.3-70b">llama-3.3-70b-versatile</option>
                  <option className="bg-background" value="mixtral-8x7b">mixtral-8x7b-32768</option>
                </select>
              </div>
              <Slider value={temperature} onChange={setTemperature} min={0} max={100} label="Temperature" unit="%" />
              <Toggle checked={streaming} onChange={() => setStreaming(!streaming)} label="Enable Streaming" />
              <Toggle checked={autoAnalyze} onChange={() => setAutoAnalyze(!autoAnalyze)} label="Auto-analyze Errors" />
            </div>
          </div>
        );
      case "blueprints":
        return (
          <div className="space-y-3">
            <Toggle checked={autoSave} onChange={() => setAutoSave(!autoSave)} label="Auto-save Successful Flows" />
            <Toggle checked={validateSelectors} onChange={() => setValidateSelectors(!validateSelectors)} label="Validate Selectors" />
          </div>
        );
      case "reports":
        return (
          <div className="space-y-6">
            <div>
              <span className="font-mono text-xs text-muted-foreground block mb-1">Default Format</span>
              <div className="flex gap-2">
                {["json", "html", "markdown"].map(f => (
                  <button key={f} onClick={() => setReportFormat(f)}
                    className={`font-mono text-xs px-4 py-2 rounded-xl border transition-all uppercase ${
                      reportFormat === f ? "border-primary/40 bg-primary/10 text-primary" : "border-glass-border text-muted-foreground hover:text-foreground"
                    }`}
                  >{f}</button>
                ))}
              </div>
            </div>
            <div className="space-y-3">
              <Toggle checked={autoExport} onChange={() => setAutoExport(!autoExport)} label="Auto-export Reports" />
              <Slider value={retentionDays} onChange={setRetentionDays} min={7} max={365} label="Retention Period" unit=" days" />
            </div>
            <div className="border-t border-glass-border pt-4 space-y-3">
              <h3 className="font-mono text-sm font-semibold text-foreground mb-2">Include in Reports</h3>
              <Toggle checked={includeScreenshots} onChange={() => setIncludeScreenshots(!includeScreenshots)} label="Screenshots" />
              <Toggle checked={includeNetwork} onChange={() => setIncludeNetwork(!includeNetwork)} label="Network Logs" />
              <Toggle checked={includeConsole} onChange={() => setIncludeConsole(!includeConsole)} label="Console Logs" />
            </div>
          </div>
        );
      case "integrations":
        return (
          <div className="space-y-4">
            {[
              { name: "Slack", desc: "Send notifications to Slack channels", connected: false },
              { name: "GitHub Actions", desc: "CI/CD integration templates", connected: true },
              { name: "Email (SMTP)", desc: "Send report emails via SMTP", connected: false },
              { name: "Webhooks", desc: "Custom webhook endpoints", connected: false },
            ].map((int) => (
              <div key={int.name} className="glass-panel-strong p-4 flex items-center justify-between">
                <div>
                  <span className="font-mono text-xs font-semibold text-foreground">{int.name}</span>
                  <p className="font-mono text-[10px] text-muted-foreground">{int.desc}</p>
                </div>
                <button className={`font-mono text-[10px] px-3 py-1.5 rounded-lg border transition-colors ${
                  int.connected
                    ? "border-emerald-400/30 text-emerald-400 bg-emerald-400/10"
                    : "border-glass-border text-muted-foreground hover:text-foreground hover:border-primary/30"
                }`}>
                  {int.connected ? "✓ Connected" : "Connect"}
                </button>
              </div>
            ))}
          </div>
        );
      case "advanced":
        return (
          <div className="space-y-6">
            <div className="space-y-3">
              <Slider value={parallelExec} onChange={setParallelExec} min={1} max={10} label="Parallel Executions" unit="" />
              <Slider value={maxRetries} onChange={setMaxRetries} min={0} max={5} label="Max Retries" unit="" />
              <Toggle checked={debugMode} onChange={() => setDebugMode(!debugMode)} label="Debug Mode" />
            </div>
            <div className="border-t border-glass-border pt-4 space-y-3">
              <h3 className="font-mono text-sm font-semibold text-foreground text-destructive mb-2">Danger Zone</h3>
              <div className="flex gap-2">
                <button className="font-mono text-[10px] px-3 py-2 rounded-xl border border-glass-border text-muted-foreground hover:text-foreground transition-colors flex items-center gap-1">
                  <RotateCcw className="w-3 h-3" /> Reset to Defaults
                </button>
                <button className="font-mono text-[10px] px-3 py-2 rounded-xl border border-destructive/30 text-destructive hover:bg-destructive/10 transition-colors flex items-center gap-1">
                  <Trash2 className="w-3 h-3" /> Clear All Data
                </button>
              </div>
            </div>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-black tracking-tight gradient-text flex items-center gap-2">
          <span>⚙️</span> Settings
        </h1>
        <p className="font-mono text-xs text-muted-foreground mt-1">Configure NPM system</p>
      </div>

      <div className="grid md:grid-cols-[200px_1fr] gap-6">
        {/* Sidebar */}
        <div className="glass-panel p-2 space-y-0.5 h-fit">
          {SECTIONS.map((section) => (
            <button
              key={section.id}
              onClick={() => setActiveSection(section.id)}
              className={`w-full flex items-center gap-2.5 px-3 py-2.5 rounded-xl font-mono text-xs transition-all ${
                activeSection === section.id
                  ? "bg-primary/10 text-primary border border-primary/20"
                  : "text-muted-foreground hover:text-foreground hover:bg-muted/20 border border-transparent"
              }`}
            >
              {section.icon}
              <span>{section.label}</span>
              <ChevronRight className="w-3 h-3 ml-auto opacity-40" />
            </button>
          ))}
        </div>

        {/* Content */}
        <GlassPanel glow="none" className="min-h-[400px]">
          <div className="flex items-center justify-between mb-6">
            <h2 className="font-mono text-sm font-semibold text-foreground uppercase tracking-wider">
              {SECTIONS.find(s => s.id === activeSection)?.label}
            </h2>
            <button className="flex items-center gap-1.5 px-4 py-2 rounded-xl font-mono text-xs bg-primary/10 text-primary border border-primary/30 hover:bg-primary/20 transition-colors">
              <Save className="w-3 h-3" /> Save Changes
            </button>
          </div>
          {renderSection()}
        </GlassPanel>
      </div>
    </div>
  );
};

export default Settings;
