function formatTime(value) {
  return value ? new Date(value).toLocaleString() : "Time unavailable";
}

function describeEvent(event, finding) {
  const details = event.details || {};
  const tool = details.tool;

  const messages = {
    AGENT_RUN_STARTED: `Run started for: ${details.message || "user request"}`,
    TOOL_REQUESTED: `Agent requested ${tool || "a tool"}${details.action ? ` (${details.action})` : ""}.`,
    TOOL_ALLOWED: `${tool || "Tool"} passed policy checks.`,
    TOOL_EXECUTED: `${tool || "Tool"} executed successfully.`,
    TOOL_BLOCKED: `${tool || "Tool"} was blocked by governance.`,
    FINDING_CREATED: `Finding created: ${details.finding_type || finding?.finding_type || "policy deviation"}.`,
    APPROVAL_REQUESTED: "Human review requested before any action can continue.",
    APPROVAL_GRANTED: `Approval granted${details.reason ? `: ${details.reason}` : "."}`,
    APPROVAL_REJECTED: `Approval rejected${details.reason ? `: ${details.reason}` : "."}`,
    AGENT_RESUMED: "Agent resumed after reviewer approval.",
    APPROVED_ACTION_EXECUTED: `${tool || "Approved action"} executed once after review.`,
    LLM_DECISION_FALLBACK: `LLM unavailable; recorded deterministic tool decision for ${tool || "the request"}.`,
    RUN_COMPLETED: `Run completed${tool ? ` using ${tool}` : ""}.`,
  };

  return messages[event.event_type] || Object.entries(details)
    .map(([key, value]) => `${key.replaceAll("_", " ")}: ${String(value)}`)
    .join(" · ");
}

export default function AuditEvents({ events, agents, findings }) {
  const agentById = new Map(agents.map((agent) => [agent.id, agent]));
  const findingById = new Map(findings.map((finding) => [finding.id, finding]));

  return (
    <section>
      <h2 className="mb-2 text-lg font-medium">Audit Timeline</h2>
      <p className="mb-4 text-sm text-white/50">
        Chronological record of every governance decision and reviewer action.
      </p>

      <div className="space-y-3">
        {events.length === 0 && (
          <p className="border border-dashed border-white/20 p-5 text-sm text-white/50">
            No audit records yet. Run the agent to begin the timeline.
          </p>
        )}

        {events.map((event) => {
          const agent = agentById.get(event.agent_id);
          const finding = findingById.get(event.finding_id);

          return (
            <article key={event.id} className="border-l-2 border-white/30 pl-5 py-1">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h3 className="text-sm font-medium">{event.event_type.replaceAll("_", " ")}</h3>
                <time className="text-xs text-white/40">{formatTime(event.created_at)}</time>
              </div>
              <p className="mt-1 text-sm text-white/70">{describeEvent(event, finding)}</p>
              <p className="mt-2 text-xs text-white/40">
                Actor: {event.actor} · Agent: {agent?.name || event.agent_id}
                {event.run_id && ` · Run: ${event.run_id.slice(0, 8)}`}
              </p>
            </article>
          );
        })}
      </div>
    </section>
  );
}
