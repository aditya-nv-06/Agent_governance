import { useState, useMemo } from "react";

const INITIAL_FORM = {
  decidedBy: "governance-admin",
  reason: "",
};

export default function Approvals({
  approvals,
  findings,
  runs,
  agents,
  onDecision,
  onExecute,
}) {
  const [filter, setFilter] = useState("pending"); // Default to 'pending' so approved items are removed from active queue
  const [forms, setForms] = useState({});
  const [loadingState, setLoadingState] = useState({});
  const [formErrors, setFormErrors] = useState({});
  const [feedback, setFeedback] = useState("");

  const findingById = useMemo(
    () => new Map(findings.map((finding) => [finding.id, finding])),
    [findings]
  );
  const runById = useMemo(
    () => new Map(runs.map((run) => [run.id, run])),
    [runs]
  );
  const agentById = useMemo(
    () => new Map(agents.map((agent) => [agent.id, agent])),
    [agents]
  );

  const pendingCount = useMemo(
    () => approvals.filter((a) => String(a.status).toUpperCase() === "PENDING").length,
    [approvals]
  );
  const approvedCount = useMemo(
    () => approvals.filter((a) => String(a.status).toUpperCase() === "APPROVED").length,
    [approvals]
  );
  const rejectedCount = useMemo(
    () => approvals.filter((a) => String(a.status).toUpperCase() === "REJECTED").length,
    [approvals]
  );

  const filteredApprovals = useMemo(() => {
    if (filter === "pending") return approvals.filter((a) => String(a.status).toUpperCase() === "PENDING");
    if (filter === "approved") return approvals.filter((a) => String(a.status).toUpperCase() === "APPROVED");
    if (filter === "rejected") return approvals.filter((a) => String(a.status).toUpperCase() === "REJECTED");
    return approvals;
  }, [approvals, filter]);

  function getForm(approvalId) {
    return forms[approvalId] || INITIAL_FORM;
  }

  function updateForm(approvalId, field, value) {
    setForms((current) => ({
      ...current,
      [approvalId]: { ...getForm(approvalId), [field]: value },
    }));
    setFormErrors((current) => ({ ...current, [approvalId]: "" }));
  }

  async function submitDecision(approvalId, approved, customReason = null) {
    const form = getForm(approvalId);
    const reviewer = form.decidedBy?.trim() || "governance-admin";
    const defaultReason = approved
      ? "Approved by governance administrator after policy review"
      : "Rejected by governance administrator due to security boundary deviation";
    const finalReason = customReason || form.reason?.trim() || defaultReason;

    setLoadingState((prev) => ({ ...prev, [approvalId]: approved ? "approving" : "rejecting" }));
    setFormErrors((prev) => ({ ...prev, [approvalId]: "" }));
    setFeedback("");

    try {
      await onDecision(approvalId, {
        approved,
        decided_by: reviewer,
        reason: finalReason,
      });
      setFeedback(
        `✓ Request ${approved ? "APPROVED" : "REJECTED"} and removed from pending review queue.`
      );
    } catch (err) {
      setFormErrors((current) => ({
        ...current,
        [approvalId]: err.message || "Failed to record decision.",
      }));
    } finally {
      setLoadingState((prev) => ({ ...prev, [approvalId]: null }));
    }
  }

  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-medium flex items-center gap-2">
            Approvals & Human Review
            {pendingCount > 0 ? (
              <span className="px-2 py-0.5 rounded text-xs bg-yellow-500/20 border border-yellow-500/40 text-yellow-300">
                ⏳ {pendingCount} Pending Review
              </span>
            ) : (
              <span className="px-2 py-0.5 rounded text-xs bg-green-500/20 border border-green-500/40 text-green-300">
                ✓ All Pending Items Resolved
              </span>
            )}
          </h2>
          <p className="mt-1 text-sm text-white/50">
            Review and decide high-risk or out-of-bounds agent actions. Approved requests are automatically removed from this pending queue.
          </p>
        </div>

        {/* Filter Badges */}
        <div className="flex flex-wrap gap-2 text-xs">
          <button
            type="button"
            onClick={() => setFilter("pending")}
            className={`px-3 py-1 border rounded-sm transition-colors ${
              filter === "pending"
                ? "bg-yellow-400 text-black font-medium border-yellow-400"
                : "border-yellow-500/40 text-yellow-300 hover:bg-yellow-500/10"
            }`}
          >
            Pending Review ({pendingCount})
          </button>
          <button
            type="button"
            onClick={() => setFilter("approved")}
            className={`px-3 py-1 border rounded-sm transition-colors ${
              filter === "approved"
                ? "bg-green-500 text-black font-medium border-green-500"
                : "border-green-500/40 text-green-300 hover:bg-green-500/10"
            }`}
          >
            History: Approved ({approvedCount})
          </button>
          <button
            type="button"
            onClick={() => setFilter("rejected")}
            className={`px-3 py-1 border rounded-sm transition-colors ${
              filter === "rejected"
                ? "bg-red-500 text-white font-medium border-red-500"
                : "border-red-500/40 text-red-300 hover:bg-red-500/10"
            }`}
          >
            History: Rejected ({rejectedCount})
          </button>
          <button
            type="button"
            onClick={() => setFilter("all")}
            className={`px-3 py-1 border rounded-sm transition-colors ${
              filter === "all" ? "bg-white text-black font-medium" : "border-white/30 text-white/70 hover:text-white"
            }`}
          >
            All ({approvals.length})
          </button>
        </div>
      </div>

      {feedback && (
        <div className="border border-green-500/40 bg-green-500/10 p-3 rounded text-xs text-green-300 flex items-center justify-between">
          <span>{feedback}</span>
          <button type="button" onClick={() => setFeedback("")} className="underline text-green-400/80">Dismiss</button>
        </div>
      )}

      <div className="space-y-3">
        {filteredApprovals.length === 0 && (
          <p className="border border-dashed border-white/20 p-5 text-sm text-white/50">
            {approvals.length === 0
              ? "No requests need review. High-risk simulated actions will queue here for human review."
              : `No approvals match the '${filter}' filter.`}
          </p>
        )}

        {filteredApprovals.map((approval) => {
          const finding = findingById.get(approval.finding_id);
          const run = finding ? runById.get(finding.run_id) : null;
          const agent = finding ? agentById.get(finding.agent_id) : null;
          const form = getForm(approval.id);
          const isPending = approval.status === "PENDING";
          const isApproved = approval.status === "APPROVED";
          const isRejected = approval.status === "REJECTED";
          const isExecuted = approval.status === "EXECUTED";
          const currentLoading = loadingState[approval.id];

          return (
            <article
              key={approval.id}
              className={`border p-5 rounded transition-all ${
                isPending
                  ? "border-yellow-500/40 bg-yellow-500/5"
                  : isApproved
                  ? "border-green-500/40 bg-green-500/5"
                  : isRejected
                  ? "border-red-500/40 bg-red-500/5"
                  : "border-white/20 bg-black"
              }`}
            >
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <p className="font-medium text-white">
                    {isPending
                      ? "Human Approval Required"
                      : isApproved
                      ? "✓ Request Approved"
                      : isRejected
                      ? "✗ Request Rejected"
                      : "Reviewed Action"}
                  </p>
                  <p className="mt-1 text-sm text-white/70">
                    {finding
                      ? <>Tool: <span className="text-white font-mono">{finding.actual}</span></>
                      : "Action awaiting reviewer decision."}
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <span
                    className={`border px-2.5 py-1 text-xs uppercase tracking-wider rounded-sm font-medium ${
                      isPending
                        ? "border-yellow-400 bg-yellow-400/20 text-yellow-200"
                        : isApproved
                        ? "border-green-400 bg-green-400/20 text-green-200"
                        : isRejected
                        ? "border-red-400 bg-red-400/20 text-red-200"
                        : "border-white/25 text-white/70"
                    }`}
                  >
                    {approval.status}
                  </span>
                </div>
              </div>

              {finding && (
                <dl className="mt-4 grid gap-x-6 gap-y-3 border-y border-white/10 py-4 text-xs sm:grid-cols-2 text-white/70">
                  <div>
                    <dt className="text-white/40">Requesting Agent</dt>
                    <dd className="mt-1 text-white font-medium">{agent?.name || finding.agent_id}</dd>
                  </div>
                  <div>
                    <dt className="text-white/40">Severity / Risk</dt>
                    <dd className="mt-1">
                      <span className={`px-2 py-0.5 rounded text-[11px] font-mono ${
                        finding.severity === "CRITICAL" ? "text-red-300 bg-red-500/20" : "text-amber-300 bg-amber-500/20"
                      }`}>
                        {finding.severity}
                      </span>
                    </dd>
                  </div>
                  <div className="sm:col-span-2">
                    <dt className="text-white/40">Policy Deviation Reason</dt>
                    <dd className="mt-1 text-white">{finding.reason}</dd>
                  </div>
                  {run?.input_message && (
                    <div className="sm:col-span-2">
                      <dt className="text-white/40">Original Context</dt>
                      <dd className="mt-1 text-white/80 font-mono text-[11px]">{run.input_message}</dd>
                    </div>
                  )}
                </dl>
              )}

              {isPending && (
                <div className="mt-4 rounded border border-white/15 bg-black/60 p-4">
                  <p className="text-sm font-medium text-white">Reviewer Decision</p>
                  <p className="mt-1 text-xs text-white/50">Record reviewer signature and decision reason (optional; smart defaults applied if blank).</p>
                  
                  <div className="mt-4 grid gap-3 sm:grid-cols-2">
                    <label className="text-xs text-white/60">
                      Reviewer Name
                      <input
                        value={form.decidedBy}
                        onChange={(event) => updateForm(approval.id, "decidedBy", event.target.value)}
                        className="mt-1 w-full border border-white/25 bg-black px-3 py-2 text-sm text-white outline-none focus:border-white rounded-sm"
                        placeholder="governance-admin"
                      />
                    </label>
                    <label className="text-xs text-white/60">
                      Decision Reason (optional)
                      <input
                        value={form.reason}
                        onChange={(event) => updateForm(approval.id, "reason", event.target.value)}
                        className="mt-1 w-full border border-white/25 bg-black px-3 py-2 text-sm text-white outline-none focus:border-white rounded-sm"
                        placeholder="Reason for approval/rejection"
                      />
                    </label>
                  </div>

                  {formErrors[approval.id] && (
                    <p className="mt-3 text-xs text-red-300 font-medium">{formErrors[approval.id]}</p>
                  )}

                  <div className="mt-4 flex flex-wrap gap-2">
                    <button
                      type="button"
                      disabled={!!currentLoading}
                      onClick={() => submitDecision(approval.id, true)}
                      className="bg-emerald-400 px-4 py-2 text-xs font-semibold text-black hover:bg-emerald-300 disabled:opacity-50 rounded-sm cursor-pointer"
                    >
                      {currentLoading === "approving" ? "Approving..." : "✓ Approve Request"}
                    </button>
                    <button
                      type="button"
                      disabled={!!currentLoading}
                      onClick={() => submitDecision(approval.id, false)}
                      className="border border-rose-400 px-4 py-2 text-xs font-semibold text-rose-300 hover:bg-rose-500/20 disabled:opacity-50 rounded-sm cursor-pointer"
                    >
                      {currentLoading === "rejecting" ? "Rejecting..." : "✗ Reject Request"}
                    </button>
                  </div>
                </div>
              )}

              {isApproved && (
                <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border border-emerald-300/40 bg-emerald-300/10 p-4 rounded">
                  <div className="text-xs text-emerald-200">
                    <strong>Approved by:</strong> {approval.decided_by || "Administrator"}
                    {approval.decision_reason && ` · "${approval.decision_reason}"`}
                  </div>
                  <div className="flex items-center gap-2">
                    {onExecute && (
                      <button
                        type="button"
                        className="bg-white px-3 py-1.5 text-xs font-medium text-black hover:bg-white/80 rounded-sm cursor-pointer"
                        onClick={() => onExecute(approval.id)}
                      >
                        Execute Approved Action
                      </button>
                    )}
                    <button
                      type="button"
                      disabled={!!currentLoading}
                      className="border border-rose-400/60 px-3 py-1.5 text-xs text-rose-300 hover:bg-rose-500/20 rounded-sm cursor-pointer"
                      onClick={() => submitDecision(approval.id, false, "Reversed approval to rejected status by administrator")}
                    >
                      {currentLoading === "rejecting" ? "Rejecting..." : "Change to Reject"}
                    </button>
                  </div>
                </div>
              )}

              {isRejected && (
                <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border border-rose-500/30 bg-rose-500/10 p-4 rounded">
                  <div className="text-xs text-rose-300">
                    <strong>Rejected by:</strong> {approval.decided_by || "Administrator"}
                    {approval.decision_reason && ` · "${approval.decision_reason}"`}
                  </div>
                  <button
                    type="button"
                    disabled={!!currentLoading}
                    className="bg-emerald-400/90 px-3 py-1.5 text-xs font-semibold text-black hover:bg-emerald-300 rounded-sm cursor-pointer"
                    onClick={() => submitDecision(approval.id, true, "Reconsidered and approved by governance administrator")}
                  >
                    {currentLoading === "approving" ? "Approving..." : "Reconsider & Approve"}
                  </button>
                </div>
              )}
            </article>
          );
        })}
      </div>
    </section>
  );
}


