import { useState } from "react";
import { simulateAgent, getAgentsAnalytics } from "../services/api";

export default function Simulate({ agents, onComplete }) {
  const [count, setCount] = useState(5);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  async function handleSimulate(agentId) {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await simulateAgent(agentId, Number(count));
      setResult(res);
      await onComplete?.();
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleRefreshAnalytics() {
    setLoading(true);
    setError(null);
    try {
      const data = await getAgentsAnalytics();
      setResult({ analytics: data });
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="border border-white/20 p-6">
      <h2 className="text-lg font-medium">Simulate Runs</h2>
      <p className="mt-1 text-sm text-white/50">Generate simulated runs for an agent (auto / approval).</p>

      <div className="mt-4 flex gap-2">
        <input value={count} onChange={(e) => setCount(e.target.value)} className="w-24 rounded-sm border bg-black px-2 py-1 text-sm" />
        <button disabled={loading} className="bg-white px-3 py-1 text-sm text-black" onClick={() => handleRefreshAnalytics()}>Refresh analytics</button>
      </div>

      <div className="mt-4 space-y-2">
        {agents.map((agent) => (
          <div key={agent.id} className="flex items-center justify-between border border-white/10 p-2">
            <div>
              <div className="font-medium">{agent.name}</div>
              <div className="text-xs text-white/60">{agent.description}</div>
            </div>
            <div className="flex gap-2">
              <button className="border px-3 py-1 text-sm" onClick={() => handleSimulate(agent.id)} disabled={loading}>Simulate</button>
            </div>
          </div>
        ))}
      </div>

      {error && <div className="mt-4 border border-white/30 p-3 text-sm">{error}</div>}

      {result && (
        <pre className="mt-4 max-h-64 overflow-auto rounded-sm bg-black/60 p-3 text-xs">{JSON.stringify(result, null, 2)}</pre>
      )}
    </section>
  );
}
