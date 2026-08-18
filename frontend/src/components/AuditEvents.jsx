import { useState, useMemo } from "react";

function formatTime(value) {
  return value ? new Date(value).toLocaleString() : "Time unavailable";
}

function parseDetails(details) {
  if (!details) return {};
  if (typeof details === "object") return details;
  try {
    return JSON.parse(details);
  } catch {
    return { info: String(details) };
  }
}

function describeEvent(event, finding) {
  const details = parseDetails(event.details);
  const tool = details.tool || details.action;

  const messages = {
    CRITICAL_SECURITY_ALERT: `🚨 CRITICAL SECURITY VIOLATION: ${details.reason || `Blocked execution of restricted tool '${tool}'`}`,
    CUSTOMER_SERVICE_REQUEST: `Customer service request: '${tool || "action"}' for ${details.customer_id || "customer"}${details.request_context ? ` · "${details.request_context}"` : ""}`,
    AGENT_RUN_STARTED: `Run started: ${details.message || "user request"}${tool ? ` (tool: ${tool})` : ""}`,
    LLM_TOOL_REQUEST: `Agent LLM proposed action '${tool || "tool"}' with arguments: ${JSON.stringify(details.arguments || {})}`,
    TOOL_REQUESTED: `Agent requested ${tool || "a tool"}${details.action ? ` (${details.action})` : ""}`,
    TOOL_ALLOWED: `Policy allowed: ${details.reason || `${tool || "Tool"} complies with standard operating policy`}`,
    TOOL_EXECUTED: `${tool || "Tool"} successfully executed by agent backend.`,
    TOOL_BLOCKED: `Blocked by policy: ${details.reason || `Tool '${tool || "action"}' blocked by security boundary`}`,
    INSTRUCTION_BLOCKED: `Out-of-scope instruction blocked: ${details.reason || details.disallowed?.join?.(", ") || "Action outside approved boundaries"}`,
    FINDING_CREATED: `Security finding recorded: ${details.reason || details.finding_type || finding?.reason || "policy deviation"}`,
    APPROVAL_REQUESTED: `Compliance signoff required${details.tool ? ` for '${details.tool}'` : ""}${details.severity ? ` [${details.severity}]` : ""}`,
    APPROVAL_GRANTED: `Reviewer approved action: ${details.reason || "Approved after compliance review"}`,
    APPROVAL_REJECTED: `Reviewer rejected action: ${details.reason || "Rejected due to policy non-compliance"}`,
    AGENT_RESUMED: "Agent resumed execution following reviewer signoff.",
    APPROVED_ACTION_EXECUTED: `Approved action '${tool || "tool"}' executed successfully once.`,
    AGENT_REGISTERED: `External agent registered into governance: '${details.name || "Agent"}' (${details.url || "URL"})`,
    WARNING_TRIGGERED: `Warning threshold reached [${details.level || "warning"}]: ${details.reason || "High LLM call frequency"}`,
    LLM_DECISION_FALLBACK: `LLM fallback: recorded deterministic decision for ${tool || "the request"}.`,
    RUN_COMPLETED: `Run completed successfully${tool ? ` using ${tool}` : ""}.`,
  };

  if (messages[event.event_type]) {
    return messages[event.event_type];
  }

  return Object.entries(details)
    .map(([key, value]) => `${key.replaceAll("_", " ")}: ${typeof value === "object" ? JSON.stringify(value) : String(value)}`)
    .join(" · ");
}

export default function AuditEvents({ events, agents, findings }) {
  const [filter, setFilter] = useState("all"); // 'all', 'security', 'customer', 'approvals'
  const [searchQuery, setSearchQuery] = useState("");

  const agentById = useMemo(
    () => new Map(agents.map((agent) => [agent.id, agent])),
    [agents]
  );
  const findingById = useMemo(
    () => new Map(findings.map((finding) => [finding.id, finding])),
    [findings]
  );

  const filteredEvents = useMemo(() => {
    let list = events;
    if (filter === "security") {
      list = list.filter((e) =>
        ["CRITICAL_SECURITY_ALERT", "TOOL_BLOCKED", "INSTRUCTION_BLOCKED", "FINDING_CREATED"].includes(e.event_type)
      );
    } else if (filter === "customer") {
      list = list.filter((e) =>
        ["CUSTOMER_SERVICE_REQUEST", "TOOL_EXECUTED", "TOOL_ALLOWED", "AGENT_RUN_STARTED"].includes(e.event_type)
      );
    } else if (filter === "approvals") {
      list = list.filter((e) =>
        ["APPROVAL_REQUESTED", "APPROVAL_GRANTED", "APPROVAL_REJECTED", "AGENT_RESUMED", "APPROVED_ACTION_EXECUTED"].includes(e.event_type)
      );
    }

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim();
      list = list.filter((e) => {
        const desc = describeEvent(e, findingById.get(e.finding_id)).toLowerCase();
        const type = e.event_type.toLowerCase();
        const actor = (e.actor || "").toLowerCase();
        const agentName = (agentById.get(e.agent_id)?.name || "").toLowerCase();
        return desc.includes(q) || type.includes(q) || actor.includes(q) || agentName.includes(q);
      });
    }

    return list;
  }, [events, filter, searchQuery, findingById, agentById]);

  const criticalEventCount = useMemo(
    () => events.filter((e) => e.event_type === "CRITICAL_SECURITY_ALERT").length,
    [events]
  );

  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-medium flex items-center gap-2">
            Audit Timeline
            <span className="px-2 py-0.5 rounded text-xs bg-white/10 border border-white/20 text-white/80">
              {events.length} Total Events
            </span>
            {criticalEventCount > 0 && (
              <span className="px-2 py-0.5 rounded text-xs bg-red-500/20 border border-red-500/40 text-red-300">
                🚨 {criticalEventCount} Critical Alerts
              </span>
            )}
          </h2>
          <p className="mt-1 text-sm text-white/50">
            Chronological audit log of all simulation runs, security evaluations, and reviewer decisions.
          </p>
        </div>

        {/* Search and Filters */}
        <div className="flex flex-wrap items-center gap-2">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search audit trail..."
            className="rounded-sm border border-white/20 bg-black px-3 py-1 text-xs text-white placeholder:text-white/40 focus:border-white"
          />
          <div className="flex flex-wrap gap-1.5 text-xs">
            <button
              type="button"
              onClick={() => setFilter("all")}
              className={`px-3 py-1 border rounded-sm transition-colors ${
                filter === "all" ? "bg-white text-black font-medium" : "border-white/30 text-white/70 hover:text-white"
              }`}
            >
              All ({events.length})
            </button>
            <button
              type="button"
              onClick={() => setFilter("security")}
              className={`px-3 py-1 border rounded-sm transition-colors ${
                filter === "security" ? "bg-red-500 text-white font-medium border-red-500" : "border-red-500/40 text-red-300 hover:bg-red-500/10"
              }`}
            >
              Security & Blocks
            </button>
            <button
              type="button"
              onClick={() => setFilter("customer")}
              className={`px-3 py-1 border rounded-sm transition-colors ${
                filter === "customer" ? "bg-blue-500 text-white font-medium border-blue-500" : "border-blue-500/40 text-blue-300 hover:bg-blue-500/10"
              }`}
            >
              Simulations
            </button>
            <button
              type="button"
              onClick={() => setFilter("approvals")}
              className={`px-3 py-1 border rounded-sm transition-colors ${
                filter === "approvals" ? "bg-yellow-500 text-black font-medium border-yellow-500" : "border-yellow-500/40 text-yellow-300 hover:bg-yellow-500/10"
              }`}
            >
              Approvals
            </button>
          </div>
        </div>
      </div>

      <div className="space-y-3">
        {filteredEvents.length === 0 && (
          <p className="border border-dashed border-white/20 p-5 text-sm text-white/50">
            {events.length === 0
              ? "No audit records yet. Run simulations or agent actions above to populate the audit timeline."
              : `No audit events matching '${filter}'${searchQuery ? ` and query '${searchQuery}'` : ""}.`}
          </p>
        )}

        {filteredEvents.map((event) => {
          const agent = agentById.get(event.agent_id);
          const finding = findingById.get(event.finding_id);
          const isCritical = event.event_type === "CRITICAL_SECURITY_ALERT";
          const isBlocked = event.event_type === "TOOL_BLOCKED" || event.event_type === "INSTRUCTION_BLOCKED";
          const isApproval = ["APPROVAL_REQUESTED", "APPROVAL_GRANTED", "APPROVAL_REJECTED"].includes(event.event_type);

          const borderStyle = isCritical
            ? "border-l-4 border-l-red-500 bg-red-500/5"
            : isBlocked
            ? "border-l-4 border-l-amber-500 bg-amber-500/5"
            : isApproval
            ? "border-l-4 border-l-yellow-400 bg-yellow-500/5"
            : "border-l-2 border-l-white/30 bg-black";

          return (
            <article key={event.id} className={`p-4 rounded-r border-t border-r border-b border-white/10 ${borderStyle}`}>
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  {isCritical && <span className="text-red-400 font-mono text-xs font-bold">🚨 [CRITICAL ALERT]</span>}
                  <h3 className="text-sm font-medium text-white capitalize">
                    {event.event_type.replaceAll("_", " ")}
                  </h3>
                </div>
                <time className="text-xs text-white/40 font-mono">{formatTime(event.created_at)}</time>
              </div>

              <p className="mt-1 text-sm text-white/80">{describeEvent(event, finding)}</p>

              <div className="mt-2 flex flex-wrap items-center gap-3 text-xs text-white/40 font-mono">
                <span>Actor: <strong className="text-white/70">{event.actor}</strong></span>
                <span>•</span>
                <span>Agent: <strong className="text-white/70">{agent?.name || event.agent_id?.slice?.(0, 8) || event.agent_id}</strong></span>
                {event.run_id && (
                  <>
                    <span>•</span>
                    <span>Run: {String(event.run_id).slice(0, 8)}...</span>
                  </>
                )}
                {event.finding_id && (
                  <>
                    <span>•</span>
                    <span className="text-red-300">Finding: {String(event.finding_id).slice(0, 8)}...</span>
                  </>
                )}
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}

