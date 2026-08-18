import { useMemo, useState } from "react";

function formatDate(value) {
  return value ? new Date(value).toLocaleString() : "Running / In-Progress";
}

function runSummary(run, auditEvents) {
  const events = auditEvents.filter((event) => event.run_id === run.id);
  const customerReq = events.find((event) => event.event_type === "CUSTOMER_SERVICE_REQUEST");
  const request = events.find((event) => event.event_type === "TOOL_REQUESTED" || event.event_type === "LLM_TOOL_REQUEST");
  const blocked = events.find((event) => event.event_type === "TOOL_BLOCKED" || event.event_type === "CRITICAL_SECURITY_ALERT");
  const executed = events.find((event) => event.event_type === "TOOL_EXECUTED");
  const approvedExecution = events.find((event) => event.event_type === "APPROVED_ACTION_EXECUTED");
  const finding = events.find((event) => event.event_type === "FINDING_CREATED");

  const toolName =
    run.tool_name ||
    customerReq?.details?.tool ||
    request?.details?.tool ||
    blocked?.details?.tool ||
    executed?.details?.tool ||
    approvedExecution?.details?.tool ||
    finding?.details?.tool ||
    "Standard action";

  const customerId = customerReq?.details?.customer_id;
  const reason = blocked?.details?.reason || finding?.details?.reason || executed?.details?.reason;

  return {
    tool: toolName,
    customerId,
    reason,
    dataSource: run.data_source || request?.details?.data_source || (customerId ? "customer_database" : "governance_engine"),
    action: run.action || request?.details?.action || toolName,
    outcome: blocked
      ? "Blocked — Human Approval Required"
      : approvedExecution
      ? "Approved Action Executed"
      : executed
      ? "Allowed & Executed"
      : run.status === "blocked"
      ? "Blocked by Policy"
      : run.status === "completed"
      ? "Completed Successfully"
      : run.status,
  };
}

export default function Runs({ runs, agents, auditEvents }) {
  const [filter, setFilter] = useState("all"); // 'all', 'completed', 'blocked', 'running'
  const agentById = useMemo(() => new Map(agents.map((agent) => [agent.id, agent])), [agents]);

  const completedCount = useMemo(() => runs.filter((r) => r.status === "completed").length, [runs]);
  const blockedCount = useMemo(() => runs.filter((r) => r.status === "blocked").length, [runs]);
  const runningCount = useMemo(() => runs.filter((r) => r.status === "running").length, [runs]);

  const filteredRuns = useMemo(() => {
    if (filter === "completed") return runs.filter((r) => r.status === "completed");
    if (filter === "blocked") return runs.filter((r) => r.status === "blocked");
    if (filter === "running") return runs.filter((r) => r.status === "running");
    return runs;
  }, [runs, filter]);

  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-medium flex items-center gap-2">
            Simulation & Agent Runs
            <span className="px-2 py-0.5 rounded text-xs bg-white/10 border border-white/20 text-white/80">
              {runs.length} Total Runs
            </span>
          </h2>
          <p className="mt-1 text-sm text-white/50">
            Complete execution history of all simulated customer requests and governed agent workflows.
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
            All Runs ({runs.length})
          </button>
          <button
            type="button"
            onClick={() => setFilter("completed")}
            className={`px-3 py-1 border rounded-sm transition-colors ${
              filter === "completed"
                ? "bg-green-500 text-black font-medium border-green-500"
                : "border-green-500/40 text-green-300 hover:bg-green-500/10"
            }`}
          >
            Completed / Allowed ({completedCount})
          </button>
          <button
            type="button"
            onClick={() => setFilter("blocked")}
            className={`px-3 py-1 border rounded-sm transition-colors ${
              filter === "blocked"
                ? "bg-red-500 text-white font-medium border-red-500"
                : "border-red-500/40 text-red-300 hover:bg-red-500/10"
            }`}
          >
            Blocked by Policy ({blockedCount})
          </button>
          {runningCount > 0 && (
            <button
              type="button"
              onClick={() => setFilter("running")}
              className={`px-3 py-1 border rounded-sm transition-colors ${
                filter === "running"
                  ? "bg-blue-500 text-white font-medium border-blue-500"
                  : "border-blue-500/40 text-blue-300 hover:bg-blue-500/10"
              }`}
            >
              Running ({runningCount})
            </button>
          )}
        </div>
      </div>

      <div className="space-y-3">
        {filteredRuns.length === 0 && (
          <p className="border border-dashed border-white/20 p-5 text-sm text-white/50">
            {runs.length === 0
              ? "No agent runs recorded yet. Use the Customer Service simulation or Run Agent above to execute requests."
              : `No runs matching the '${filter}' filter.`}
          </p>
        )}

        {filteredRuns.map((run) => {
          const agent = agentById.get(run.agent_id);
          const summary = runSummary(run, auditEvents);
          const isBlocked = run.status === "blocked";
          const isCompleted = run.status === "completed";

          return (
            <article
              key={run.id}
              className={`border p-5 rounded transition-all ${
                isBlocked
                  ? "border-amber-500/40 bg-amber-500/5"
                  : isCompleted
                  ? "border-white/20 bg-black"
                  : "border-blue-500/40 bg-blue-500/5"
              }`}
            >
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <h3 className="font-medium text-white">{agent?.name || "Customer Service Agent"}</h3>
                    {summary.customerId && (
                      <span className="font-mono text-xs px-2 py-0.5 rounded bg-white/10 text-white/80">
                        {summary.customerId}
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-white/70">Request: {run.input_message}</p>
                </div>
                <span
                  className={`border px-3 py-1 text-xs uppercase tracking-wider rounded-sm font-medium ${
                    isBlocked
                      ? "border-red-500/60 bg-red-500/15 text-red-300"
                      : isCompleted
                      ? "border-green-500/60 bg-green-500/15 text-green-300"
                      : "border-blue-500/60 bg-blue-500/15 text-blue-300"
                  }`}
                >
                  {run.status}
                </span>
              </div>

              <div className="mt-4 grid gap-2 border-y border-white/10 py-3 text-xs text-white/60 sm:grid-cols-2">
                <p>
                  Requested tool: <span className="text-white font-mono">{summary.tool}</span>
                </p>
                <p>
                  Governance result:{" "}
                  <span
                    className={`font-medium ${
                      isBlocked ? "text-red-300" : isCompleted ? "text-green-300" : "text-white"
                    }`}
                  >
                    {summary.outcome}
                  </span>
                </p>
                <p>
                  Data source: <span className="text-white">{summary.dataSource}</span>
                </p>
                <p>
                  Action: <span className="text-white">{summary.action}</span>
                </p>
              </div>

              {summary.reason && (
                <div className="mt-3 text-xs text-amber-200/90 bg-amber-500/10 border border-amber-500/20 p-2.5 rounded">
                  Policy note: {summary.reason}
                </div>
              )}

              <div className="mt-3 flex flex-wrap items-center justify-between gap-2 text-xs text-white/40 font-mono">
                <span>Run ID: {String(run.id).slice(0, 12)}...</span>
                <span>
                  Started: {formatDate(run.created_at)}
                  {run.completed_at && ` · Completed: ${formatDate(run.completed_at)}`}
                </span>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}
