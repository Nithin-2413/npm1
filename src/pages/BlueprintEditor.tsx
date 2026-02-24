import { useState } from "react";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { GlassPanel } from "@/components/GlassPanel";
import { ActionBadge, ActionType } from "@/components/ActionBadge";
import {
  Save, Play, X, Plus, Trash2, GripVertical, Wand2,
  ChevronRight, Variable
} from "lucide-react";

interface EditorAction {
  id: string;
  type: ActionType;
  selector: string;
  value: string;
  timeout: number;
  optional: boolean;
}

const BlueprintEditor = () => {
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

  const addAction = (type: ActionType) => {
    const newAction: EditorAction = {
      id: Date.now().toString(),
      type,
      selector: "",
      value: "",
      timeout: 5000,
      optional: false,
    };
    setActions([...actions, newAction]);
    setSelectedAction(newAction.id);
  };

  const removeAction = (id: string) => {
    setActions(actions.filter(a => a.id !== id));
    if (selectedAction === id) setSelectedAction(null);
  };

  const updateAction = (id: string, updates: Partial<EditorAction>) => {
    setActions(actions.map(a => a.id === id ? { ...a, ...updates } : a));
  };

  const selected = actions.find(a => a.id === selectedAction);

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Top Bar */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <Link to="/blueprints" className="font-mono text-xs text-muted-foreground hover:text-foreground transition-colors">
            ← Blueprints
          </Link>
          <span className="text-muted-foreground">/</span>
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="bg-transparent font-mono text-lg font-bold text-foreground outline-none border-b border-transparent hover:border-glass-border focus:border-primary/40 transition-colors"
          />
        </div>
        <div className="flex items-center gap-2">
          <span className="font-mono text-[9px] text-muted-foreground">Auto-saved 2m ago</span>
          <button className="flex items-center gap-1.5 px-3 py-2 rounded-xl font-mono text-xs border border-glass-border text-muted-foreground hover:text-foreground transition-colors">
            <Save className="w-3 h-3" /> Save Draft
          </button>
          <button className="flex items-center gap-1.5 px-4 py-2 rounded-xl font-mono text-xs bg-primary/20 text-primary border border-primary/30 hover:bg-primary/30 transition-colors">
            <Play className="w-3 h-3" /> Save & Run
          </button>
        </div>
      </div>

      <div className="grid lg:grid-cols-[200px_1fr_280px] gap-6">
        {/* Left Panel - Action Library */}
        <div className="glass-panel p-3 h-fit space-y-3">
          <span className="font-mono text-[10px] text-muted-foreground uppercase tracking-wider">Action Library</span>
          {ACTION_LIBRARY.map((cat) => (
            <div key={cat.category}>
              <span className="font-mono text-[9px] text-muted-foreground uppercase tracking-wider">{cat.category}</span>
              <div className="mt-1 space-y-1">
                {cat.actions.map((action) => (
                  <button
                    key={action.type}
                    onClick={() => addAction(action.type)}
                    className="w-full flex items-center gap-2 px-2 py-2 rounded-lg text-left hover:bg-muted/20 transition-colors group"
                  >
                    <ActionBadge type={action.type} />
                    <div className="flex-1 min-w-0">
                      <div className="font-mono text-[10px] text-foreground/80 group-hover:text-foreground">{action.label}</div>
                      <div className="font-mono text-[8px] text-muted-foreground">{action.desc}</div>
                    </div>
                    <Plus className="w-3 h-3 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Center - Flow Canvas */}
        <GlassPanel glow="cyan" className="min-h-[500px]">
          <div className="flex items-center gap-2 mb-4">
            <span className="text-lg">📐</span>
            <h3 className="font-mono text-sm font-semibold tracking-wider uppercase text-primary">Flow Builder</h3>
            <div className="flex-1 h-px bg-gradient-to-r from-primary/30 to-transparent" />
          </div>

          {/* Start node */}
          <div className="flex items-center gap-2 mb-2 px-3 py-2 rounded-lg bg-emerald-400/10 border border-emerald-400/20">
            <span className="text-emerald-400 font-mono text-xs font-bold">● START</span>
          </div>
          <div className="ml-5 border-l-2 border-glass-border pl-4 space-y-2">
            {actions.map((action, i) => (
              <motion.div
                key={action.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                className={`flex items-center gap-2 px-3 py-2.5 rounded-lg border cursor-pointer transition-all ${
                  selectedAction === action.id
                    ? "border-primary/40 bg-primary/10 ring-1 ring-primary/20"
                    : "border-glass-border hover:border-primary/20 hover:bg-muted/10"
                }`}
                onClick={() => setSelectedAction(action.id)}
              >
                <GripVertical className="w-3 h-3 text-muted-foreground/40 cursor-grab" />
                <ActionBadge type={action.type} />
                <span className="font-mono text-xs text-foreground/70 flex-1 truncate">
                  {action.selector || action.value || "(empty)"}
                </span>
                <button
                  onClick={(e) => { e.stopPropagation(); removeAction(action.id); }}
                  className="text-muted-foreground hover:text-destructive transition-colors opacity-0 group-hover:opacity-100"
                >
                  <X className="w-3 h-3" />
                </button>
              </motion.div>
            ))}
          </div>

          {/* Add action */}
          <button
            onClick={() => addAction("click")}
            className="w-full mt-3 flex items-center justify-center gap-2 px-4 py-3 rounded-xl border border-dashed border-glass-border text-muted-foreground hover:text-primary hover:border-primary/30 transition-colors font-mono text-xs"
          >
            <Plus className="w-3.5 h-3.5" /> Add Action
          </button>
        </GlassPanel>

        {/* Right Panel - Properties */}
        <div className="space-y-4">
          {selected ? (
            <GlassPanel glow="purple" className="h-fit">
              <div className="flex items-center gap-2 mb-4">
                <Wand2 className="w-4 h-4 text-secondary" />
                <h3 className="font-mono text-sm font-semibold tracking-wider uppercase text-secondary">Properties</h3>
              </div>

              <div className="space-y-3">
                <div>
                  <label className="font-mono text-[10px] text-muted-foreground uppercase tracking-wider block mb-1">Action Type</label>
                  <select
                    value={selected.type}
                    onChange={(e) => updateAction(selected.id, { type: e.target.value as ActionType })}
                    className="w-full bg-muted/20 border border-glass-border rounded-xl px-3 py-2 font-mono text-xs text-foreground outline-none cursor-pointer"
                  >
                    <option className="bg-background" value="navigate">Navigate</option>
                    <option className="bg-background" value="fill">Fill</option>
                    <option className="bg-background" value="click">Click</option>
                    <option className="bg-background" value="select">Select</option>
                    <option className="bg-background" value="wait">Wait</option>
                    <option className="bg-background" value="assert">Assert</option>
                    <option className="bg-background" value="screenshot">Screenshot</option>
                  </select>
                </div>

                <div>
                  <label className="font-mono text-[10px] text-muted-foreground uppercase tracking-wider block mb-1">Selector</label>
                  <input
                    value={selected.selector}
                    onChange={(e) => updateAction(selected.id, { selector: e.target.value })}
                    placeholder="e.g. input#email, button.submit"
                    className="w-full bg-muted/20 border border-glass-border rounded-xl px-3 py-2 font-mono text-xs text-foreground placeholder:text-muted-foreground outline-none focus:ring-1 focus:ring-primary/40"
                  />
                </div>

                <div>
                  <label className="font-mono text-[10px] text-muted-foreground uppercase tracking-wider block mb-1">Value</label>
                  <input
                    value={selected.value}
                    onChange={(e) => updateAction(selected.id, { value: e.target.value })}
                    placeholder="Value or {{VARIABLE}}"
                    className="w-full bg-muted/20 border border-glass-border rounded-xl px-3 py-2 font-mono text-xs text-foreground placeholder:text-muted-foreground outline-none focus:ring-1 focus:ring-primary/40"
                  />
                </div>

                <div>
                  <label className="font-mono text-[10px] text-muted-foreground uppercase tracking-wider block mb-1">Timeout: {selected.timeout}ms</label>
                  <input
                    type="range" min={1000} max={30000} step={1000}
                    value={selected.timeout}
                    onChange={(e) => updateAction(selected.id, { timeout: parseInt(e.target.value) })}
                    className="w-full h-1 bg-muted/40 rounded-full appearance-none accent-primary"
                  />
                </div>

                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox" checked={selected.optional}
                    onChange={(e) => updateAction(selected.id, { optional: e.target.checked })}
                    className="accent-primary"
                  />
                  <span className="font-mono text-xs text-muted-foreground">Optional (skip on failure)</span>
                </label>

                <button
                  onClick={() => removeAction(selected.id)}
                  className="w-full flex items-center justify-center gap-1 px-3 py-2 rounded-xl font-mono text-xs border border-destructive/30 text-destructive hover:bg-destructive/10 transition-colors mt-4"
                >
                  <Trash2 className="w-3 h-3" /> Delete Action
                </button>
              </div>
            </GlassPanel>
          ) : (
            <div className="glass-panel p-6 flex flex-col items-center justify-center text-center">
              <Wand2 className="w-6 h-6 text-muted-foreground/30 mb-2" />
              <p className="font-mono text-xs text-muted-foreground">Select an action to edit properties</p>
            </div>
          )}

          {/* Variables */}
          <GlassPanel glow="none" className="h-fit">
            <div className="flex items-center gap-2 mb-3">
              <Variable className="w-4 h-4 text-primary" />
              <h3 className="font-mono text-[10px] font-semibold tracking-wider uppercase text-primary">Variables</h3>
            </div>
            <div className="space-y-2">
              {variables.map((v, i) => (
                <div key={i} className="flex items-center gap-2 font-mono text-[11px]">
                  <span className="text-secondary w-28 truncate">{`{{${v.name}}}`}</span>
                  <input
                    value={v.defaultValue}
                    onChange={(e) => {
                      const updated = [...variables];
                      updated[i].defaultValue = e.target.value;
                      setVariables(updated);
                    }}
                    className="flex-1 bg-muted/20 border border-glass-border rounded-lg px-2 py-1 text-foreground/70 outline-none focus:ring-1 focus:ring-primary/40"
                  />
                  <button
                    onClick={() => setVariables(variables.filter((_, j) => j !== i))}
                    className="text-muted-foreground hover:text-destructive transition-colors"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                </div>
              ))}
              <button
                onClick={() => setVariables([...variables, { name: "NEW_VAR", defaultValue: "", type: "text" }])}
                className="w-full flex items-center justify-center gap-1 px-3 py-2 rounded-lg border border-dashed border-glass-border text-muted-foreground hover:text-primary hover:border-primary/30 transition-colors font-mono text-[10px]"
              >
                <Plus className="w-3 h-3" /> Add Variable
              </button>
            </div>
          </GlassPanel>
        </div>
      </div>
    </div>
  );
};

export default BlueprintEditor;
