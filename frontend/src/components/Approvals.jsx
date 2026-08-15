export default function Approvals({
  approvals,
  onDecision,
  onExecute,
}) {

  return (

    <section>

      <h2 className="mb-4 text-lg font-medium">
        Approvals
      </h2>


      <div className="space-y-3">

        {approvals.map((approval) => (

          <div
            key={approval.id}
            className="flex items-center justify-between border border-white/20 p-5"
          >

            <div>

              <p className="font-medium">
                Approval Request
              </p>

              <p className="mt-1 text-sm text-white/50">
                {approval.decision_reason || `Requested by ${approval.requested_by}`}
              </p>

            </div>


            <div className="flex items-center gap-2">
              {approval.status === "PENDING" && (
                <>
                  <button className="border border-white px-2 py-1 text-xs hover:bg-white hover:text-black" onClick={() => onDecision(approval.id, true)}>Approve</button>
                  <button className="border border-white/30 px-2 py-1 text-xs text-white/70 hover:border-white" onClick={() => onDecision(approval.id, false)}>Reject</button>
                </>
              )}
              {approval.status === "APPROVED" && (
                <button className="border border-white px-2 py-1 text-xs hover:bg-white hover:text-black" onClick={() => onExecute(approval.id)}>
                  Execute
                </button>
              )}
              <span className="border border-white/25 px-3 py-1 text-xs uppercase tracking-wider text-white/70">
                {approval.status}
              </span>
            </div>

          </div>

        ))}

      </div>

    </section>
  );
}
