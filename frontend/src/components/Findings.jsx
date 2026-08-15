const severityStyle = {
  CRITICAL: "border-rose-300 text-rose-200",
  HIGH: "border-amber-300 text-amber-200",
};

export default function Findings({ findings, agents, approvals }) {
  const agentById = new Map(agents.map((agent) => [agent.id, agent]));
  const approvalByFindingId = new Map(
    approvals.map((approval) => [approval.finding_id, approval])
  );

  return (
    <section>
      <h2 className="mb-2 text-lg font-medium">Security Findings</h2>
      <p className="mb-4 text-sm text-white/50">
        A finding explains the policy deviation, its risk, and its current review state.
      </p>

      <div className="space-y-3">
        {findings.length === 0 && (
          <p className="border border-dashed border-white/20 p-5 text-sm text-white/50">
            No deviations detected. Run “Get customer information” to see the blocked-tool scenario.
          </p>
        )}

        {findings.map((finding) => {
          const agent = agentById.get(finding.agent_id);
          const approval = approvalByFindingId.get(finding.id);

          return (
            <article key={finding.id} className="border border-white/20 p-5">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h3 className="font-medium">{finding.finding_type.replaceAll("_", " ")}</h3>
                  <p className="mt-1 text-sm text-white/50">{finding.reason}</p>
                </div>
                <div className="flex gap-2">
                  <span className={`border px-3 py-1 text-xs uppercase tracking-wider ${severityStyle[finding.severity] || "border-white/25 text-white/70"}`}>
                    {finding.severity}
                  </span>
                  <span className="border border-white/25 px-3 py-1 text-xs uppercase tracking-wider text-white/70">
                    {finding.status}
                  </span>
                </div>
              </div>

              <div className="mt-4 grid gap-2 border-y border-white/10 py-3 text-xs text-white/60 sm:grid-cols-2">
                <p>Agent: <span className="text-white">{agent?.name || finding.agent_id}</span></p>
                <p>Review: <span className="text-white">{approval?.status || "Not required"}</span></p>
                <p>Expected: <span className="text-white">{finding.expected}</span></p>
                <p>Actual request: <span className="text-white">{finding.actual}</span></p>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}
