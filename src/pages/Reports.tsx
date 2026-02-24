import { useState } from "react";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { GlassPanel } from "@/components/GlassPanel";
import { StatusBadge, StatusType } from "@/components/StatusBadge";
import {
  Search, Download, Filter, Eye, RotateCcw, Trash2, MoreHorizontal,
  ChevronLeft, ChevronRight, ArrowUpDown
} from "lucide-react";

interface Report {
  id: string;
  command: string;
  blueprint?: string;
  status: StatusType;
  startTime: string;
  duration: string;
  actionsCompleted: string;
  networkRequests: number;
  errors: number;
}

const REPORTS: Report[] = [
  { id: "exec_001", command: "Navigate to signup, fill form, submit", blueprint: "signup_flow_v1", status: "success", startTime: "2026-02-24 14:32", duration: "6.5s", actionsCompleted: "7/7", networkRequests: 8, errors: 0 },
  { id: "exec_002", command: "Run blueprint: login_flow_v1", blueprint: "login_flow_v1", status: "success", startTime: "2026-02-24 14:25", duration: "2.1s", actionsCompleted: "5/5", networkRequests: 4, errors: 0 },
  { id: "exec_003", command: "Test checkout with expired card", status: "failure", startTime: "2026-02-24 14:18", duration: "4.8s", actionsCompleted: "2/4", networkRequests: 6, errors: 2 },
  { id: "exec_004", command: "Verify dashboard widgets load", status: "success", startTime: "2026-02-24 14:10", duration: "3.2s", actionsCompleted: "3/3", networkRequests: 12, errors: 0 },
  { id: "exec_005", command: "Fill profile settings, upload avatar", status: "partial", startTime: "2026-02-24 13:55", duration: "5.1s", actionsCompleted: "4/6", networkRequests: 9, errors: 1 },
  { id: "exec_006", command: "Run signup_flow_v1 with random data", blueprint: "signup_flow_v1", status: "success", startTime: "2026-02-24 13:40", duration: "7.2s", actionsCompleted: "7/7", networkRequests: 8, errors: 0 },
  { id: "exec_007", command: "Test password reset flow", status: "success", startTime: "2026-02-24 12:30", duration: "4.1s", actionsCompleted: "6/6", networkRequests: 5, errors: 0 },
  { id: "exec_008", command: "Verify email verification link", status: "failure", startTime: "2026-02-24 12:15", duration: "8.3s", actionsCompleted: "3/5", networkRequests: 7, errors: 3 },
  { id: "exec_009", command: "Test multi-language switching", status: "success", startTime: "2026-02-24 11:45", duration: "3.8s", actionsCompleted: "4/4", networkRequests: 3, errors: 0 },
  { id: "exec_010", command: "Run full regression suite", status: "partial", startTime: "2026-02-24 11:00", duration: "45.2s", actionsCompleted: "18/22", networkRequests: 42, errors: 4 },
];

const Reports = () => {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<"all" | StatusType>("all");
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [page, setPage] = useState(1);
  const perPage = 8;

  const filtered = REPORTS
    .filter(r => {
      const matchSearch = !search || r.command.toLowerCase().includes(search.toLowerCase());
      const matchStatus = statusFilter === "all" || r.status === statusFilter;
      return matchSearch && matchStatus;
    });

  const paginated = filtered.slice((page - 1) * perPage, page * perPage);
  const totalPages = Math.ceil(filtered.length / perPage);

  const toggleSelect = (id: string) => {
    setSelectedIds(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);
  };

  const toggleAll = () => {
    if (selectedIds.length === paginated.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(paginated.map(r => r.id));
    }
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-black tracking-tight gradient-text flex items-center gap-2">
            <span>📋</span> Execution Reports
          </h1>
          <p className="font-mono text-xs text-muted-foreground mt-1">{REPORTS.length} total executions</p>
        </div>
        <div className="flex items-center gap-2">
          <select className="glass-panel-strong px-3 py-2 rounded-xl font-mono text-xs text-foreground bg-transparent outline-none cursor-pointer">
            <option className="bg-background">Last 7 Days</option>
            <option className="bg-background">Last 30 Days</option>
            <option className="bg-background">Last 90 Days</option>
            <option className="bg-background">All Time</option>
          </select>
          <button className="flex items-center gap-2 px-3 py-2 rounded-xl font-mono text-xs border border-glass-border text-muted-foreground hover:text-foreground transition-colors">
            <Download className="w-3.5 h-3.5" /> Export
          </button>
        </div>
      </div>

      {/* Search & Filters */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="flex-1 min-w-[200px] max-w-md glass-panel-strong flex items-center gap-2 px-3 py-2 rounded-xl">
          <Search className="w-3.5 h-3.5 text-muted-foreground" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by command..."
            className="flex-1 bg-transparent font-mono text-xs text-foreground placeholder:text-muted-foreground outline-none"
          />
        </div>
        <div className="flex items-center gap-1">
          {(["all", "success", "failure", "partial"] as const).map(f => (
            <button
              key={f}
              onClick={() => { setStatusFilter(f); setPage(1); }}
              className={`font-mono text-[10px] px-2.5 py-1.5 rounded-lg border transition-all capitalize ${
                statusFilter === f
                  ? "border-primary/40 bg-primary/10 text-primary"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              }`}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {/* Bulk Actions */}
      {selectedIds.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-panel glass-glow-cyan p-3 flex items-center gap-3"
        >
          <span className="font-mono text-xs text-primary">{selectedIds.length} selected</span>
          <button className="font-mono text-[10px] px-3 py-1.5 rounded-lg border border-destructive/30 text-destructive hover:bg-destructive/10 transition-colors flex items-center gap-1">
            <Trash2 className="w-3 h-3" /> Delete
          </button>
          <button className="font-mono text-[10px] px-3 py-1.5 rounded-lg border border-primary/30 text-primary hover:bg-primary/10 transition-colors flex items-center gap-1">
            <Download className="w-3 h-3" /> Export
          </button>
          <button
            onClick={() => setSelectedIds([])}
            className="ml-auto font-mono text-[10px] text-muted-foreground hover:text-foreground transition-colors"
          >
            Clear
          </button>
        </motion.div>
      )}

      {/* Table */}
      <GlassPanel glow="none">
        {/* Table Header */}
        <div className="grid grid-cols-[32px_auto_1fr_100px_70px_70px_70px_60px_60px] gap-2 px-3 py-2.5 font-mono text-[9px] text-muted-foreground uppercase tracking-wider border-b border-glass-border items-center">
          <input
            type="checkbox"
            checked={selectedIds.length === paginated.length && paginated.length > 0}
            onChange={toggleAll}
            className="accent-primary w-3.5 h-3.5"
          />
          <span className="w-8">St</span>
          <span>Command</span>
          <span>Time</span>
          <span>Duration</span>
          <span>Actions</span>
          <span>Network</span>
          <span>Errors</span>
          <span></span>
        </div>

        {/* Rows */}
        <div className="divide-y divide-glass-border/30">
          {paginated.map((report) => (
            <div
              key={report.id}
              className={`grid grid-cols-[32px_auto_1fr_100px_70px_70px_70px_60px_60px] gap-2 px-3 py-2.5 items-center hover:bg-muted/10 transition-colors ${
                selectedIds.includes(report.id) ? "bg-primary/5" : ""
              }`}
            >
              <input
                type="checkbox"
                checked={selectedIds.includes(report.id)}
                onChange={() => toggleSelect(report.id)}
                className="accent-primary w-3.5 h-3.5"
              />
              <StatusBadge status={report.status} className="border-0 bg-transparent px-0 gap-0 w-8" />
              <div className="min-w-0">
                <Link to={`/reports/${report.id}`} className="font-mono text-xs text-foreground hover:text-primary transition-colors truncate block">
                  {report.command}
                </Link>
                {report.blueprint && (
                  <span className="font-mono text-[9px] text-secondary">📐 {report.blueprint}</span>
                )}
              </div>
              <span className="font-mono text-[10px] text-muted-foreground">{report.startTime.split(" ")[1]}</span>
              <span className="font-mono text-[10px] text-muted-foreground">{report.duration}</span>
              <span className="font-mono text-[10px] text-primary">{report.actionsCompleted}</span>
              <span className="font-mono text-[10px] text-muted-foreground">{report.networkRequests}</span>
              <span className={`font-mono text-[10px] font-bold ${report.errors > 0 ? "text-destructive" : "text-muted-foreground"}`}>{report.errors}</span>
              <div className="flex gap-1">
                <Link to={`/reports/${report.id}`} className="p-1 rounded text-muted-foreground hover:text-primary transition-colors">
                  <Eye className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          ))}
        </div>

        {/* Pagination */}
        <div className="flex items-center justify-between px-3 py-3 border-t border-glass-border">
          <span className="font-mono text-[10px] text-muted-foreground">
            Showing {(page - 1) * perPage + 1}-{Math.min(page * perPage, filtered.length)} of {filtered.length}
          </span>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setPage(Math.max(1, page - 1))}
              disabled={page === 1}
              className="p-1.5 rounded-lg border border-glass-border text-muted-foreground hover:text-foreground disabled:opacity-30 transition-colors"
            >
              <ChevronLeft className="w-3.5 h-3.5" />
            </button>
            {Array.from({ length: totalPages }, (_, i) => (
              <button
                key={i}
                onClick={() => setPage(i + 1)}
                className={`font-mono text-[10px] w-7 h-7 rounded-lg transition-colors ${
                  page === i + 1 ? "bg-primary/20 text-primary border border-primary/30" : "text-muted-foreground hover:text-foreground"
                }`}
              >
                {i + 1}
              </button>
            ))}
            <button
              onClick={() => setPage(Math.min(totalPages, page + 1))}
              disabled={page === totalPages}
              className="p-1.5 rounded-lg border border-glass-border text-muted-foreground hover:text-foreground disabled:opacity-30 transition-colors"
            >
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </GlassPanel>
    </div>
  );
};

export default Reports;
