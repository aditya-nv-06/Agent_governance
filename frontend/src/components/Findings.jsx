import { useState, useMemo } from "react";

const severityStyle = {
  CRITICAL: "border-red-500/80 bg-red-500/20 text-red-200 font-semibold shadow-sm shadow-red-500/20",
  HIGH: "border-amber-400/70 bg-amber-500/15 text-amber-200 font-medium",
  MEDIUM: "border-yellow-400/60 bg-yellow-500/10 text-yellow-200",
  LOW: "border-blue-400/60 bg-blue-500/10 text-blue-200",
};

export default function Findings({ findings, agents, approvals, onDecision }) {
  const [filter, setFilter] = useState("all"); // 'all', 'critical', 'high', 'open'
  const [actionLoading, setActionLoading] = useState({});

  const agentById = useMemo(
    () => new Map(agents.map((agent) => [agent.id, agent])),
    [agents]
  );
  const approvalByFindingId = useMemo(
    () => new Map(approvals.map((approval) => [approval.finding_id, approval])),
    [approvals]
  );

  const criticalCount = useMemo(
    () => findings.filter((f) => f.severity === "CRITICAL").length,
    [findings]
  );
  const highCount = useMemo(
    () => findings.filter((f) => f.severity === "HIGH").length,
    [findings]
  );
  const openCount = useMemo(
    () => findings.filter((f) => f.status === "open" || !f.status).length,
    [findings]
  );

  const filteredFindings = useMemo(() => {
    if (filter === "critical") return findings.filter((f) => f.severity === "CRITICAL");
    if (filter === "high") return findings.filter((f) => f.severity === "HIGH");
    if (filter === "open") return findings.filter((f) => f.status === "open" || !f.status);
    return findings;
  }, [findings, filter]);

  async function handleQuickDecision(approvalId, approved) {
    if (!onDecision || !approvalId) return;
    setActionLoading((prev) => ({ ...prev, [approvalId]: approved ? "approving" : "rejecting" }));
    try {
      await onDecision(approvalId, {
        approved,
        decided_by: "governance-admin",
        reason: approved
          ? "Approved by administrator via Security Findings review"
          : "Rejected by administrator via Security Findings review",
      });
    } catch {
      // Handled upstream
    } finally {
      setActionLoading((prev) => ({ ...prev, [approvalId]: null }));
    }
  }

  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-medium flex items-center gap-2">
            Security Findings
            {criticalCount > 0 && (
              <span className="px-2 py-0.5 rounded text-xs bg-red-500/20 border border-red-500/40 text-red-300 animate-pulse">
                🚨 {criticalCount} Critical
              </span>
            )}
          </h2>
          <p className="mt-1 text-sm text-white/50">
            Detected policy deviations, critical security violations, and human review states.
          </p>
        </div>

        {/* Filter Badges */}
        <div className="flex flex-wrap gap-2 text-xs">
          <button
            type="button"
            onClick={() => setFilter("all")}
            className={`px-3 py-1 border rounded-sm transition-colors ${
              filter === "all" ? "bg-white text-black font-medium" : "border-white/30 text-white/70 hover:text-white"
            }`}
          >
            All ({findings.length})
          </button>
          <button
            type="button"
            onClick={() => setFilter("critical")}
            className={`px-3 py-1 border rounded-sm transition-colors ${
              filter === "critical" ? "bg-red-500 text-white font-medium border-red-500" : "border-red-500/40 text-red-300 hover:bg-red-500/10"
            }`}
          >
            Critical ({criticalCount})
          </button>
          <button
            type="button"
            onClick={() => setFilter("high")}
            className={`px-3 py-1 border rounded-sm transition-colors ${
              filter === "high" ? "bg-amber-500 text-black font-medium border-amber-500" : "border-amber-500/40 text-amber-300 hover:bg-amber-500/10"
            }`}
          >
            High ({highCount})
          </button>
          <button
            type="button"
            onClick={() => setFilter("open")}
            className={`px-3 py-1 border rounded-sm transition-colors ${
              filter === "open" ? "bg-white text-black font-medium" : "border-white/30 text-white/70 hover:text-white"
            }`}
          >
            Open ({openCount})
          </button>
        </div>
      </div>

      <div className="space-y-3">
        {filteredFindings.length === 0 && (
          <p className="border border-dashed border-white/20 p-5 text-sm text-white/50">
            {findings.length === 0
              ? "No security deviations detected. Run Customer Service simulation with high-risk actions to inspect findings."
              : `No findings match the '${filter}' filter.`}
          </p>
        )}

        {filteredFindings.map((finding) => {
          const agent = agentById.get(finding.agent_id);
          const approval = approvalByFindingId.get(finding.id);
          const isCritical = finding.severity === "CRITICAL";
          const isPendingApproval = String(approval?.status).toUpperCase() === "PENDING";
          const currentLoading = approval ? actionLoading[approval.id] : null;

          return (
            <article
              key={finding.id}
              className={`border p-5 rounded transition-all ${
                isCritical
                  ? "border-red-500/60 bg-red-500/5 shadow-sm shadow-red-500/10"
                  : "border-white/20 bg-black"
              }`}
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    {isCritical && (
                      <span className="text-red-400 text-xs font-mono font-bold tracking-wider">
                        [CRITICAL ALERT]
                      </span>
                    )}
                    <h3 className="font-medium text-white capitalize">
                      {finding.finding_type.replaceAll("_", " ")}
                    </h3>
                  </div>
                  <p className="text-sm text-white/80">{finding.reason}</p>
                </div>

                <div className="flex items-center gap-2">
                  <span
                    className={`border px-2.5 py-1 text-xs uppercase tracking-wider rounded-sm ${
                      severityStyle[finding.severity] || "border-white/25 text-white/70"
                    }`}
                  >
                    {finding.severity === "CRITICAL" ? "🚨 CRITICAL" : finding.severity}
                  </span>
                  <span
                    className={`border px-2.5 py-1 text-xs uppercase tracking-wider rounded-sm ${
                      finding.status === "open"
                        ? "border-amber-400/50 bg-amber-500/10 text-amber-200"
                        : finding.status === "approved"
                        ? "border-green-400/50 bg-green-500/10 text-green-200"
                        : "border-white/25 text-white/70"
                    }`}
                  >
                    {finding.status || "open"}
                  </span>
                </div>
              </div>

              <div className="mt-4 grid gap-2 border-y border-white/10 py-3 text-xs text-white/60 sm:grid-cols-2">
                <p>
                  Agent: <span className="text-white font-medium">{agent?.name || finding.agent_id}</span>
                </p>
                <p>
                  Human Review:{" "}
                  <span
                    className={`font-medium ${
                      approval?.status === "PENDING"
                        ? "text-yellow-300"
                        : approval?.status === "APPROVED"
                        ? "text-green-300"
                        : "text-white"
                    }`}
                  >
                    {approval ? `Decision: ${approval.status}` : "Not required / Blocked directly"}
                  </span>
                </p>
                <p>
                  Expected: <span className="text-white/80">{finding.expected}</span>
                </p>
                <p>
                  Actual Request: <span className="text-white font-mono text-[11px]">{finding.actual}</span>
                </p>
              </div>

              {isPendingApproval && (
                <div className="mt-3 flex flex-wrap items-center justify-between gap-2 border border-yellow-500/30 bg-yellow-500/10 p-3 rounded text-xs">
                  <span className="text-yellow-200 font-medium">Pending Human Approval</span>
                  <div className="flex gap-2">
                    <button
                      type="button"
                      disabled={!!currentLoading}
                      onClick={() => handleQuickDecision(approval.id, true)}
                      className="bg-emerald-400 px-3 py-1 text-xs font-semibold text-black hover:bg-emerald-300 disabled:opacity-50 rounded-sm cursor-pointer"
                    >
                      {currentLoading === "approving" ? "Approving..." : "✓ Quick Approve"}
                    </button>
                    <button
                      type="button"
                      disabled={!!currentLoading}
                      onClick={() => handleQuickDecision(approval.id, false)}
                      className="border border-rose-400 px-3 py-1 text-xs font-semibold text-rose-300 hover:bg-rose-500/20 disabled:opacity-50 rounded-sm cursor-pointer"
                    >
                      {currentLoading === "rejecting" ? "Rejecting..." : "✗ Quick Reject"}
                    </button>
                  </div>
                </div>
              )}

              <div className="mt-2 flex items-center justify-between text-[11px] text-white/40 font-mono">
                <span>Finding ID: {finding.id}</span>
                {finding.created_at && (
                  <span>{new Date(finding.created_at).toLocaleString()}</span>
                )}
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}

