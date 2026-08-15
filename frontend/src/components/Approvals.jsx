import { useState } from "react";

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
  const [forms, setForms] = useState({});
  const [formErrors, setFormErrors] = useState({});
  const findingById = new Map(findings.map((finding) => [finding.id, finding]));
  const runById = new Map(runs.map((run) => [run.id, run]));
  const agentById = new Map(agents.map((agent) => [agent.id, agent]));

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

  async function submitDecision(approvalId, approved) {
    const form = getForm(approvalId);
    if (!form.decidedBy.trim() || !form.reason.trim()) {
      setFormErrors((current) => ({
        ...current,
        [approvalId]: "Reviewer name and decision reason are required.",
      }));
      return;
    }

    await onDecision(approvalId, {
      approved,
      decided_by: form.decidedBy.trim(),
      reason: form.reason.trim(),
    });
  }

  return (
    <section>
      <h2 className="mb-2 text-lg font-medium">Approvals</h2>
      <p className="mb-4 text-sm text-white/50">
        In-profile requests execute automatically. Use this review form only for requests outside the agent’s approved scope.
      </p>

      <div className="space-y-3">
        {approvals.length === 0 && (
          <p className="border border-dashed border-white/20 p-5 text-sm text-white/50">
            No requests need review. Run “Get customer information” to create the demo approval.
          </p>
        )}

        {approvals.map((approval) => {
          const finding = findingById.get(approval.finding_id);
          const run = finding ? runById.get(finding.run_id) : null;
          const agent = finding ? agentById.get(finding.agent_id) : null;
          const form = getForm(approval.id);
          const isPending = approval.status === "PENDING";
          const isApproved = approval.status === "APPROVED";
          const isExecuted = approval.status === "EXECUTED";

          return (
            <article key={approval.id} className="border border-white/20 p-5">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <p className="font-medium">Human approval required</p>
                  <p className="mt-1 text-sm text-white/50">
                    {finding
                      ? <>The agent requested <span className="text-white">{finding.actual}</span>, outside its approved profile.</>
                      : "The requested action is awaiting reviewer decision."}
                  </p>
                </div>
                <span className="border border-white/25 px-3 py-1 text-xs uppercase tracking-wider text-white/70">
                  {approval.status}
                </span>
              </div>

              {finding && (
                <dl className="mt-4 grid gap-x-6 gap-y-3 border-y border-white/10 py-4 text-sm sm:grid-cols-2">
                  <div><dt className="text-xs text-white/40">Requesting agent</dt><dd className="mt-1">{agent?.name || finding.agent_id}</dd></div>
                  <div><dt className="text-xs text-white/40">Requested tool</dt><dd className="mt-1">{finding.actual}</dd></div>
                  <div><dt className="text-xs text-white/40">Risk</dt><dd className="mt-1">{finding.severity}</dd></div>
                  <div><dt className="text-xs text-white/40">Why escalation is required</dt><dd className="mt-1">{finding.reason}</dd></div>
                  <div className="sm:col-span-2"><dt className="text-xs text-white/40">Original user question</dt><dd className="mt-1 text-white">{run?.input_message || "Question unavailable"}</dd></div>
                </dl>
              )}

              {isPending && (
                <div className="mt-4 rounded border border-white/15 bg-white/5 p-4">
                  <p className="text-sm font-medium">Reviewer decision</p>
                  <p className="mt-1 text-xs text-white/50">Record who reviewed this request and why it is being approved or rejected.</p>
                  <div className="mt-4 grid gap-3 sm:grid-cols-2">
                    <label className="text-xs text-white/60">
                      Reviewer name
                      <input
                        value={form.decidedBy}
                        onChange={(event) => updateForm(approval.id, "decidedBy", event.target.value)}
                        className="mt-1 w-full border border-white/25 bg-black px-3 py-2 text-sm text-white outline-none focus:border-white"
                        placeholder="e.g. governance-admin"
                      />
                    </label>
                    <label className="text-xs text-white/60">
                      Decision reason
                      <input
                        value={form.reason}
                        onChange={(event) => updateForm(approval.id, "reason", event.target.value)}
                        className="mt-1 w-full border border-white/25 bg-black px-3 py-2 text-sm text-white outline-none focus:border-white"
                        placeholder="Explain this decision"
                      />
                    </label>
                  </div>
                  {formErrors[approval.id] && <p className="mt-3 text-xs text-rose-200">{formErrors[approval.id]}</p>}
                  <div className="mt-4 flex flex-wrap gap-2">
                    <button className="bg-emerald-300 px-3 py-2 text-xs font-medium text-black hover:bg-emerald-200" onClick={() => submitDecision(approval.id, true)}>Approve request</button>
                    <button className="border border-rose-300 px-3 py-2 text-xs text-rose-100 hover:bg-rose-300 hover:text-black" onClick={() => submitDecision(approval.id, false)}>Reject request</button>
                  </div>
                </div>
              )}

              {isApproved && (
                <div className="mt-4 flex flex-wrap items-center gap-3 border border-emerald-300/40 bg-emerald-300/10 p-4">
                  <p className="text-sm text-emerald-100">Approved by {approval.decided_by}. Execute this exact reviewed action once.</p>
                  <button className="bg-white px-3 py-2 text-xs font-medium text-black hover:bg-white/80" onClick={() => onExecute(approval.id)}>Execute approved action</button>
                </div>
              )}

              {!isPending && !isApproved && (
                <p className={`mt-4 text-sm ${isExecuted ? "text-emerald-200" : "text-white/60"}`}>
                  {isExecuted
                    ? "Executed once. This reviewed action is complete and cannot run again."
                    : `Rejected by ${approval.decided_by || "reviewer"}: ${approval.decision_reason || "No reason recorded"}`}
                </p>
              )}
            </article>
          );
        })}
      </div>
    </section>
  );
}
