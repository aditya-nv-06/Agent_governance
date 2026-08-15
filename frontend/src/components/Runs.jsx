import { useEffect, useMemo, useState } from "react";

const RUN_VISIBILITY_MS = 15_000;

function formatDate(value) {
  return value ? new Date(value).toLocaleString() : "Not completed";
}

function runSummary(run, auditEvents) {
  const events = auditEvents.filter((event) => event.run_id === run.id);
  const request = events.find((event) => event.event_type === "TOOL_REQUESTED");
  const blocked = events.find((event) => event.event_type === "TOOL_BLOCKED");
  const executed = events.find((event) => event.event_type === "TOOL_EXECUTED");
  const approvedExecution = events.find((event) => event.event_type === "APPROVED_ACTION_EXECUTED");

  return {
    tool: run.tool_name || request?.details?.tool || approvedExecution?.details?.tool || "No tool recorded",
    dataSource: run.data_source || request?.details?.data_source || "—",
    action: run.action || request?.details?.action || "—",
    outcome: blocked
      ? "Blocked — human approval required"
      : approvedExecution
        ? "Approved action executed"
        : executed
          ? "Allowed and executed"
          : run.status,
  };
}

export default function Runs({ runs, agents, auditEvents }) {
  const [now, setNow] = useState(Date.now());
  const agentById = new Map(agents.map((agent) => [agent.id, agent]));

  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 1_000);
    return () => window.clearInterval(timer);
  }, []);

  const visibleRuns = useMemo(() => runs.filter((run) => {
    const startedAt = new Date(run.created_at).getTime();
    return Number.isNaN(startedAt) || now - startedAt < RUN_VISIBILITY_MS;
  }), [runs, now]);

  return (
    <section>
      <h2 className="mb-2 text-lg font-medium">Live Agent Runs</h2>
      <p className="mb-4 text-sm text-white/50">
        Recent allow/block results stay visible for 15 seconds, then remain in the Audit Timeline.
      </p>

      <div className="space-y-3">
        {visibleRuns.length === 0 && (
          <p className="border border-dashed border-white/20 p-5 text-sm text-white/50">
            No live runs. Use Run Agent to create one.
          </p>
        )}

        {visibleRuns.map((run) => {
          const agent = agentById.get(run.agent_id);
          const summary = runSummary(run, auditEvents);

          return (
            <article key={run.id} className="border border-white/20 p-5">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <h3 className="font-medium">{agent?.name || "Unknown agent"}</h3>
                  <p className="mt-1 text-sm text-white/50">User request: {run.input_message}</p>
                  <p className="mt-2 font-mono text-xs text-white/40">Run ID: {run.id}</p>
                </div>
                <span className="border border-white/25 px-3 py-1 text-xs uppercase tracking-wider text-white/70">
                  {run.status}
                </span>
              </div>

              <div className="mt-4 grid gap-2 border-y border-white/10 py-3 text-xs text-white/60 sm:grid-cols-2">
                <p>Requested tool: <span className="text-white">{summary.tool}</span></p>
                <p>Governance result: <span className="text-white">{summary.outcome}</span></p>
                <p>Data source: <span className="text-white">{summary.dataSource}</span></p>
                <p>Action: <span className="text-white">{summary.action}</span></p>
              </div>

              <p className="mt-3 text-xs text-white/40">
                Started: {formatDate(run.created_at)} · Completed: {formatDate(run.completed_at)}
              </p>
            </article>
          );
        })}
      </div>
    </section>
  );
}
