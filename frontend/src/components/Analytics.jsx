export default function Analytics({ analytics }) {
  return (
    <section className="border border-white/20 p-6">
      <h2 className="text-lg font-medium">Agents Analytics</h2>
      <p className="mt-1 text-sm text-white/50">Simple per-agent metrics from simulated and real runs.</p>

      <div className="mt-4 space-y-3">
        {analytics?.length === 0 && <p className="text-sm text-white/50">No analytics data available.</p>}
        {analytics?.map((a) => (
          <div key={a.agent_id} className="flex items-center justify-between border border-white/10 p-3">
            <div>
              <div className="font-medium">{a.agent_name}</div>
              <div className="text-xs text-white/60">Runs: {a.runs_count} · Approvals: {a.approvals_count}</div>
            </div>
            <div className="text-xs text-white/60">Auto: {a.auto_executed} · Blocked: {a.blocked_count}</div>
          </div>
        ))}
      </div>
    </section>
  );
}
