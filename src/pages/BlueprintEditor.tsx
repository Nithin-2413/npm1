import { useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { GlassPanel } from "@/components/GlassPanel";
import { ActionBadge, ActionType } from "@/components/ActionBadge";
import { toast } from "sonner";
import {
  Save, Play, X, Plus, Trash2, GripVertical, Wand2,
  ChevronUp, ChevronDown, Variable, Copy, ArrowLeft
} from "lucide-react";

interface EditorAction {
  id: string;
  type: ActionType;
  selector: string;
  value: string;
  timeout: number;
  optional: boolean;
}

const ACTION_LIBRARY: { category: string; actions: { type: ActionType; label: string; desc: string }[] }[] = [
  { category: "Navigation", actions: [
    { type: "navigate", label: "Navigate", desc: "Go to URL" },
    { type: "wait", label: "Wait for URL", desc: "Wait for URL pattern" },
  ]},
  { category: "Input", actions: [
    { type: "fill", label: "Fill Input", desc: "Type into field" },
    { type: "select", label: "Select Option", desc: "Choose dropdown" },
  ]},
  { category: "Interaction", actions: [
    { type: "click", label: "Click", desc: "Click element" },
    { type: "screenshot", label: "Screenshot", desc: "Capture screenshot" },
  ]},
  { category: "Assertions", actions: [
    { type: "assert", label: "Assert", desc: "Verify element" },
  ]},
];

const BlueprintEditor = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const isViewMode = location.pathname.endsWith("/view");

  const [name, setName] = useState("New Blueprint");
  const [selectedAction, setSelectedAction] = useState<string | null>(null);
  const [actions, setActions] = useState<EditorAction[]>([
    { id: "1", type: "navigate", selector: "", value: "https://example.com/signup", timeout: 5000, optional: false },
    { id: "2", type: "fill", selector: "input#email", value: "{{USER_EMAIL}}", timeout: 5000, optional: false },
    { id: "3", type: "fill", selector: "input#password", value: "{{PASSWORD}}", timeout: 5000, optional: false },
    { id: "4", type: "click", selector: "button#submit", value: "", timeout: 5000, optional: false },
  ]);
  const [variables, setVariables] = useState([
    { name: "USER_EMAIL", defaultValue: "test@example.com", type: "text" },
    { name: "PASSWORD", defaultValue: "S3cureP@ss!", type: "text" },
  ]);

  const addAction = useCallback((type: ActionType) => {
    const newAction: EditorAction = {
      id: Date.now().toString(),
      type, selector: "", value: "", timeout: 5000, optional: false,
    };
    setActions(prev => [...prev, newAction]);
    setSelectedAction(newAction.id);
  }, []);

  const removeAction = useCallback((id: string) => {
    setActions(prev => prev.filter(a => a.id !== id));
    setSelectedAction(prev => prev === id ? null : prev);
  }, []);

  const updateAction = useCallback((id: string, updates: Partial<EditorAction>) => {
    setActions(prev => prev.map(a => a.id === id ? { ...a, ...updates } : a));
  }, []);

  const moveAction = useCallback((id: string, direction: "up" | "down") => {
    setActions(prev => {
      const idx = prev.findIndex(a => a.id === id);
      if (idx < 0) return prev;
      const target = direction === "up" ? idx - 1 : idx + 1;
      if (target < 0 || target >= prev.length) return prev;
      const next = [...prev];
      [next[idx], next[target]] = [next[target], next[idx]];
      return next;
    });
  }, []);

  const duplicateAction = useCallback((id: string) => {
    setActions(prev => {
      const idx = prev.findIndex(a => a.id === id);
      if (idx < 0) return prev;
      const clone = { ...prev[idx], id: Date.now().toString() };
      const next = [...prev];
      next.splice(idx + 1, 0, clone);
      return next;
    });
  }, []);

  const saveDraft = useCallback(() => {
    const data = { name, actions, variables };
    localStorage.setItem(`blueprint-draft-${name}`, JSON.stringify(data));
    toast.success(`Blueprint "${name}" saved as draft`);
  }, [name, actions, variables]);

  const saveAndRun = useCallback(() => {
    saveDraft();
    toast.success(`Blueprint "${name}" saved. Navigating to execute...`);
  }, [saveDraft, name]);

  const selected = actions.find(a => a.id === selectedAction);

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate("/blueprints")}
            className="flex items-center gap-1.5 font-mono text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowLeft className="w-4 h-4" /> Back
          </button>
          <span className="text-muted-foreground/30">|</span>
          {isViewMode ? (
            <h1 className="font-mono text-lg font-bold text-foreground">{name}</h1>
          ) : (
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="bg-transparent font-mono text-lg font-bold text-foreground outline-none border-b border-transparent hover:border-glass-border focus:border-primary/40 transition-colors"
            />
          )}
          {isViewMode && (
            <span className="font-mono text-[10px] px-2 py-0.5 rounded-md bg-muted/20 text-muted-foreground border border-glass-border">View Only</span>
          )}
        </div>
        {!isViewMode && (
          <div className="flex items-center gap-2">
            <span className="font-mono text-[9px] text-muted-foreground">Auto-saved 2m ago</span>
            <button onClick={saveDraft} className="flex items-center gap-1.5 px-3 py-2 rounded-xl font-mono text-xs border border-glass-border text-muted-foreground hover:text-foreground transition-colors">
              <Save className="w-3 h-3" /> Save Draft
            </button>
            <button onClick={saveAndRun} className="flex items-center gap-1.5 px-4 py-2 rounded-xl font-mono text-xs bg-primary/20 text-primary border border-primary/30 hover:bg-primary/30 transition-colors">
              <Play className="w-3 h-3" /> Save & Run
            </button>
          </div>
        )}
      </div>

      <div className="grid lg:grid-cols-[200px_1fr_280px] gap-6">
        {/* Left Panel - Action Library */}
        {!isViewMode && (
          <GlassPanel glow="none" className="p-4 h-fit space-y-4">
            <span className="font-mono text-[10px] text-muted-foreground uppercase tracking-wider">Action Library</span>
            {ACTION_LIBRARY.map((cat) => (
              <div key={cat.category}>
                <span className="font-mono text-[9px] text-muted-foreground uppercase tracking-wider">{cat.category}</span>
                <div className="mt-1.5 space-y-1">
                  {cat.actions.map((action) => (
                    <button
                      key={action.type}
                      onClick={() => addAction(action.type)}
                      className="w-full flex items-center gap-2 px-2.5 py-2.5 rounded-lg text-left hover:bg-muted/20 transition-colors group"
                    >
                      <ActionBadge type={action.type} />
                      <div className="flex-1 min-w-0">
                        <div className="font-mono text-[11px] text-foreground/80 group-hover:text-foreground">{action.label}</div>
                        <div className="font-mono text-[9px] text-muted-foreground">{action.desc}</div>
                      </div>
                      <Plus className="w-3 h-3 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </GlassPanel>
        )}

        {/* Center - Flow Canvas */}
        <GlassPanel glow="none" className={`p-6 ${isViewMode ? "lg:col-span-2" : ""}`}>
          <div className="flex items-center gap-2 mb-5">
            <h3 className="font-mono text-sm font-semibold tracking-wider uppercase text-primary">Flow Builder</h3>
            <div className="flex-1 h-px bg-gradient-to-r from-primary/30 to-transparent" />
            <span className="font-mono text-[10px] text-muted-foreground">{actions.length} actions</span>
          </div>

          {/* Start node */}
          <div className="flex items-center gap-2 mb-3 px-4 py-2.5 rounded-lg bg-emerald-400/10 border border-emerald-400/20">
            <span className="text-emerald-400 font-mono text-xs font-bold">START</span>
          </div>

          <div className="ml-6 border-l-2 border-glass-border pl-5 space-y-2.5">
            {actions.map((action, i) => (
              <motion.div
                key={action.id}
                layout
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -10 }}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg border cursor-pointer transition-all group ${
                  selectedAction === action.id
                    ? "border-primary/40 bg-primary/10 ring-1 ring-primary/20"
                    : "border-glass-border hover:border-primary/20 hover:bg-muted/10"
                }`}
                onClick={() => setSelectedAction(action.id)}
              >
                {!isViewMode && (
                  <div className="flex flex-col gap-0.5">
                    <button
                      onClick={(e) => { e.stopPropagation(); moveAction(action.id, "up"); }}
                      disabled={i === 0}
                      className="text-muted-foreground/40 hover:text-foreground disabled:opacity-20 transition-colors"
                    >
                      <ChevronUp className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={(e) => { e.stopPropagation(); moveAction(action.id, "down"); }}
                      disabled={i === actions.length - 1}
                      className="text-muted-foreground/40 hover:text-foreground disabled:opacity-20 transition-colors"
                    >
                      <ChevronDown className="w-3.5 h-3.5" />
                    </button>
                  </div>
                )}
                <ActionBadge type={action.type} />
                <span className="font-mono text-xs text-foreground/70 flex-1 truncate">
                  {action.selector || action.value || "(empty)"}
                </span>
                {!isViewMode && (
                  <div className="flex gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button onClick={(e) => { e.stopPropagation(); duplicateAction(action.id); }} className="text-muted-foreground hover:text-primary transition-colors" title="Duplicate">
                      <Copy className="w-3.5 h-3.5" />
                    </button>
                    <button onClick={(e) => { e.stopPropagation(); removeAction(action.id); }} className="text-muted-foreground hover:text-destructive transition-colors" title="Delete">
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                )}
              </motion.div>
            ))}
          </div>

          {/* End node */}
          <div className="flex items-center gap-2 mt-3 ml-6 pl-5 border-l-2 border-glass-border">
            <div className="px-4 py-2.5 rounded-lg bg-destructive/10 border border-destructive/20">
              <span className="text-destructive font-mono text-xs font-bold">END</span>
            </div>
          </div>

          {/* Add action */}
          {!isViewMode && (
            <button
              onClick={() => addAction("click")}
              className="w-full mt-4 flex items-center justify-center gap-2 px-4 py-3.5 rounded-xl border border-dashed border-glass-border text-muted-foreground hover:text-primary hover:border-primary/30 transition-colors font-mono text-xs"
            >
              <Plus className="w-3.5 h-3.5" /> Add Action
            </button>
          )}
        </GlassPanel>

        {/* Right Panel - Properties & Variables */}
        <div className="space-y-5">
          {selected ? (
            <GlassPanel glow="none" className="p-5">
              <div className="flex items-center gap-2 mb-4">
                <Wand2 className="w-4 h-4 text-secondary" />
                <h3 className="font-mono text-sm font-semibold tracking-wider uppercase text-secondary">Properties</h3>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="font-mono text-[10px] text-muted-foreground uppercase tracking-wider block mb-1.5">Action Type</label>
                  <select
                    value={selected.type}
                    disabled={isViewMode}
                    onChange={(e) => updateAction(selected.id, { type: e.target.value as ActionType })}
                    className="w-full bg-muted/20 border border-glass-border rounded-xl px-3 py-2.5 font-mono text-xs text-foreground outline-none cursor-pointer disabled:opacity-60"
                  >
                    {["navigate", "fill", "click", "select", "wait", "assert", "screenshot"].map(t => (
                      <option key={t} className="bg-background" value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="font-mono text-[10px] text-muted-foreground uppercase tracking-wider block mb-1.5">Selector</label>
                  <input
                    value={selected.selector}
                    disabled={isViewMode}
                    onChange={(e) => updateAction(selected.id, { selector: e.target.value })}
                    placeholder="e.g. input#email, button.submit"
                    className="w-full bg-muted/20 border border-glass-border rounded-xl px-3 py-2.5 font-mono text-xs text-foreground placeholder:text-muted-foreground outline-none focus:ring-1 focus:ring-primary/40 disabled:opacity-60"
                  />
                </div>

                <div>
                  <label className="font-mono text-[10px] text-muted-foreground uppercase tracking-wider block mb-1.5">Value</label>
                  <input
                    value={selected.value}
                    disabled={isViewMode}
                    onChange={(e) => updateAction(selected.id, { value: e.target.value })}
                    placeholder="Value or {{VARIABLE}}"
                    className="w-full bg-muted/20 border border-glass-border rounded-xl px-3 py-2.5 font-mono text-xs text-foreground placeholder:text-muted-foreground outline-none focus:ring-1 focus:ring-primary/40 disabled:opacity-60"
                  />
                </div>

                <div>
                  <label className="font-mono text-[10px] text-muted-foreground uppercase tracking-wider block mb-1.5">Timeout: {selected.timeout}ms</label>
                  <input
                    type="range" min={1000} max={30000} step={1000}
                    value={selected.timeout}
                    disabled={isViewMode}
                    onChange={(e) => updateAction(selected.id, { timeout: parseInt(e.target.value) })}
                    className="w-full h-1 bg-muted/40 rounded-full appearance-none accent-primary disabled:opacity-60"
                  />
                </div>

                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox" checked={selected.optional}
                    disabled={isViewMode}
                    onChange={(e) => updateAction(selected.id, { optional: e.target.checked })}
                    className="accent-primary"
                  />
                  <span className="font-mono text-xs text-muted-foreground">Optional (skip on failure)</span>
                </label>

                {!isViewMode && (
                  <button
                    onClick={() => removeAction(selected.id)}
                    className="w-full flex items-center justify-center gap-1 px-3 py-2.5 rounded-xl font-mono text-xs border border-destructive/30 text-destructive hover:bg-destructive/10 transition-colors mt-2"
                  >
                    <Trash2 className="w-3 h-3" /> Delete Action
                  </button>
                )}
              </div>
            </GlassPanel>
          ) : (
            <GlassPanel glow="none" className="p-6 flex flex-col items-center justify-center text-center">
              <Wand2 className="w-6 h-6 text-muted-foreground/30 mb-2" />
              <p className="font-mono text-xs text-muted-foreground">Select an action to {isViewMode ? "view" : "edit"} properties</p>
            </GlassPanel>
          )}

          {/* Variables */}
          <GlassPanel glow="none" className="p-5">
            <div className="flex items-center gap-2 mb-4">
              <Variable className="w-4 h-4 text-primary" />
              <h3 className="font-mono text-[10px] font-semibold tracking-wider uppercase text-primary">Variables</h3>
            </div>
            <div className="space-y-2.5">
              {variables.map((v, i) => (
                <div key={i} className="flex items-center gap-2 font-mono text-[11px]">
                  <input
                    value={v.name}
                    disabled={isViewMode}
                    onChange={(e) => {
                      const updated = [...variables];
                      updated[i].name = e.target.value.toUpperCase().replace(/[^A-Z0-9_]/g, "");
                      setVariables(updated);
                    }}
                    className="w-28 bg-muted/20 border border-glass-border rounded-lg px-2 py-1.5 text-secondary outline-none focus:ring-1 focus:ring-primary/40 disabled:opacity-60"
                  />
                  <input
                    value={v.defaultValue}
                    disabled={isViewMode}
                    onChange={(e) => {
                      const updated = [...variables];
                      updated[i].defaultValue = e.target.value;
                      setVariables(updated);
                    }}
                    className="flex-1 bg-muted/20 border border-glass-border rounded-lg px-2 py-1.5 text-foreground/70 outline-none focus:ring-1 focus:ring-primary/40 disabled:opacity-60"
                  />
                  {!isViewMode && (
                    <button
                      onClick={() => setVariables(variables.filter((_, j) => j !== i))}
                      className="text-muted-foreground hover:text-destructive transition-colors"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  )}
                </div>
              ))}
              {!isViewMode && (
                <button
                  onClick={() => setVariables([...variables, { name: "NEW_VAR", defaultValue: "", type: "text" }])}
                  className="w-full flex items-center justify-center gap-1 px-3 py-2.5 rounded-lg border border-dashed border-glass-border text-muted-foreground hover:text-primary hover:border-primary/30 transition-colors font-mono text-[10px]"
                >
                  <Plus className="w-3 h-3" /> Add Variable
                </button>
              )}
            </div>
          </GlassPanel>
        </div>
      </div>
    </div>
  );
};

export default BlueprintEditor;
