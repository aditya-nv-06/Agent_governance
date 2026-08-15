export default function Stats({ agents, activeRuns, openFindings, pendingApprovals }) {
  const stats = [
    ["Agents", agents],
    ["Active runs", activeRuns],
    ["Open findings", openFindings],
    ["Pending approvals", pendingApprovals],
  ];

  return (
    <div className="grid grid-cols-2 border border-white/20 md:grid-cols-4">
      {stats.map(([label, value]) => (
        <div className="border-b border-r border-white/20 p-5 last:border-r-0 md:border-b-0" key={label}>
          <p className="text-xs uppercase tracking-[0.18em] text-white/50">{label}</p>
          <p className="mt-3 text-3xl font-medium tabular-nums">{value}</p>
        </div>
      ))}
    </div>
  );
}
