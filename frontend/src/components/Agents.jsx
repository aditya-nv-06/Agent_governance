import { useState, useEffect } from "react";
import { registerEnvAgent, getEnvAgents, triggerEnvAgent, getEnvLogs } from "../services/api";

export default function Agents({
  agents,
  profiles,
  onCreateAgent,
  onDeleteAgent,
  onCreateProfile,
  onSimulate,
}) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [profileName, setProfileName] = useState("");
  const [allowedTools, setAllowedTools] = useState("");
  const [allowedData, setAllowedData] = useState("");
  const [allowedActions, setAllowedActions] = useState("");
  const [maxLlmCalls, setMaxLlmCalls] = useState("1000");
  const [warningThreshold, setWarningThreshold] = useState("80");
  const [criticalThreshold, setCriticalThreshold] = useState("90");
  const [error, setError] = useState("");
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [deletingId, setDeletingId] = useState(null);
  const [deleteError, setDeleteError] = useState("");
  const [simLoadingId, setSimLoadingId] = useState(null);
  const [simResult, setSimResult] = useState(null);
  const [showProfileForm, setShowProfileForm] = useState({});
  const [profileForm, setProfileForm] = useState({});
  const [envName, setEnvName] = useState("");
  const [envUrl, setEnvUrl] = useState("");
  const [envPurpose, setEnvPurpose] = useState("");
  const [envAllowed, setEnvAllowed] = useState("");
  const [envAgents, setEnvAgents] = useState([]);
  const [envLogs, setEnvLogs] = useState([]);
  const [envLoading, setEnvLoading] = useState(false);
  const [showLogsFor, setShowLogsFor] = useState(null);

  function parseList(value) {
    return (value || "").split(",").map((item) => item.trim()).filter(Boolean);
  }

  // Internal agent creation removed — external environment agents only

  async function loadEnvAgents() {
    try {
      const list = await getEnvAgents();
      setEnvAgents(list || []);
    } catch {
      setEnvAgents([]);
      setError("Failed to load environment agents. You may need to login or start the backend (check VITE_API_URL).");
    }
  }

  useEffect(() => {
    loadEnvAgents();
  }, []);

  // Auto-refresh logs when a specific agent's logs are shown
  useEffect(() => {
    if (!showLogsFor) return;
    const id = showLogsFor;
    loadLogs(id);
    const t = setInterval(() => loadLogs(id), 3000);
    return () => clearInterval(t);
  }, [showLogsFor]);

  async function createEnvAgent(e) {
    e.preventDefault();
    if (!envName || !envUrl) return;
    setEnvLoading(true);
    setError("");
    try {
      const allowedList = (envAllowed || "").split(",").map((s) => s.trim()).filter(Boolean);
      await registerEnvAgent({ name: envName, url: envUrl, purpose: envPurpose, allowed_instructions: allowedList });
      setEnvName("");
      setEnvUrl("");
      setEnvPurpose("");
      setEnvAllowed("");
      await loadEnvAgents();
      await onSimulate?.();
    } catch (err) {
      setError(err?.message || "Failed to register environment agent");
    } finally {
      setEnvLoading(false);
    }
  }

  async function triggerEnv(agentId) {
    setEnvLoading(true);
    try {
      await triggerEnvAgent(agentId, { message: "Hello from UI" });
      await loadLogs(agentId);
      await onSimulate?.();
    } catch (err) {
      // ignore
    } finally {
      setEnvLoading(false);
    }
  }

  async function loadLogs(agentId = null) {
    try {
      const logs = await getEnvLogs(agentId);
      setEnvLogs(logs || []);
      setShowLogsFor(agentId);
    } catch {
      setEnvLogs([]);
    }
  }

  return (

    <section>

      <div className="mb-4 flex items-center justify-between gap-4">
        <div><h2 className="text-lg font-medium">Agents</h2><p className="mt-1 text-sm text-white/50">Create and monitor agents governed by policy.</p></div>
      </div>

      <div className="mt-8">
        <h3 className="text-sm font-medium">Environment Agents (external URL)</h3>
        <form onSubmit={createEnvAgent} className="mt-3 flex gap-2">
          <input placeholder="Name" value={envName} onChange={(e) => setEnvName(e.target.value)} className="border px-2 py-1 bg-black text-white" />
          <input placeholder="URL" value={envUrl} onChange={(e) => setEnvUrl(e.target.value)} className="border px-2 py-1 bg-black text-white w-1/3" />
          <input placeholder="Purpose" value={envPurpose} onChange={(e) => setEnvPurpose(e.target.value)} className="border px-2 py-1 bg-black text-white" />
          <input placeholder="Allowed instructions (comma-separated)" value={envAllowed} onChange={(e) => setEnvAllowed(e.target.value)} className="border px-2 py-1 bg-black text-white w-1/4" />
          <button className="bg-white px-3 py-1 text-xs text-black" disabled={envLoading}>{envLoading ? "Saving…" : "Register"}</button>
        </form>

        <div className="mt-4 space-y-2">
            <div className="flex gap-2 mb-2">
            <button
              className="border px-2 py-1 text-xs"
              onClick={async () => {
                const lang = envAgents.find((x) => x.name === "langraph-demo");
                if (!lang) {
                  setError("langraph-demo not found. Refresh agents or ensure the backend has auto-registered the demo agent.");
                  return;
                }
                setEnvLoading(true);
                try {
                  await triggerEnvAgent(lang.id, { message: "Run demo workflow", instructions: ["read_faq", "invalid_action"] });
                  await loadLogs(lang.id);
                } catch (err) {
                  setError(err?.message || "Simulation failed");
                } finally {
                  setEnvLoading(false);
                }
              }}
              disabled={envLoading}
            >
              {envLoading ? "Simulating…" : "Simulate Langraph"}
            </button>
            <button className="border px-2 py-1 text-xs" onClick={() => { setError(""); loadEnvAgents(); }}>Refresh agents</button>
          </div>
          {envAgents.map((a) => (
            <div key={a.id} className="flex items-center justify-between border p-2">
              <div>
                <div className="font-medium">{a.name}</div>
                <div className="text-xs text-white/60">{a.url} · {a.purpose}</div>
                {a.allowed_instructions && a.allowed_instructions.length > 0 && (
                  <div className="text-xs text-white/50">Allowed: {a.allowed_instructions.join(", ")}</div>
                )}
              </div>
              <div className="flex gap-2">
                <button className="border px-2 py-1 text-xs" onClick={() => triggerEnv(a.id)}>Trigger</button>
                <button className="border px-2 py-1 text-xs" onClick={() => loadLogs(a.id)}>View logs</button>
              </div>
            </div>
          ))}
        </div>

        {showLogsFor && (
          <div className="mt-3 border p-3 bg-white/5">
            <h4 className="text-xs font-medium">Logs (latest)</h4>
            <div className="mt-2 text-xs">
              {envLogs.length === 0 && <div className="text-white/60">No logs</div>}
              {envLogs.map((l, i) => (
                <div key={i} className="mt-2 border-t pt-2">
                  <div className="font-mono text-xs text-white/60">{l.timestamp}</div>
                  <div className="text-sm">Request: {JSON.stringify(l.request)}</div>
                  <div className="text-sm">Response: {typeof l.response === 'string' ? l.response : JSON.stringify(l.response)}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="mb-4">
        <div><h2 className="text-lg font-medium">Agents</h2><p className="mt-1 text-sm text-white/50">External environment agent integration only.</p></div>
      </div>


      <div className="space-y-3">

        {deleteError && <p className="text-xs text-rose-200">{deleteError}</p>}

        {agents.map((agent) => {
          const profile = profiles.find((item) => item.agent_id === agent.id);

          return (

          <article
            key={agent.id}
            className="border border-white/20 p-5"
          >
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>

                <h3 className="font-medium">
                  {agent.name}
                </h3>

                <p className="mt-1 text-sm text-white/50">
                  {agent.description}
                </p>

                <p className="mt-3 font-mono text-xs text-white/40">
                  Agent ID: {agent.id}
                </p>
              </div>

              <span className="border border-white/25 px-3 py-1 text-xs uppercase tracking-wider text-white/70">
                {agent.status}
              </span>
            </div>

            {profile ? (
              <div className="mt-4 grid gap-2 border-t border-white/10 pt-3 text-xs text-white/60 sm:grid-cols-2">
                <p>Allowed tools: <span className="text-white">{profile.allowed_tools.join(", ") || "none"}</span></p>
                <p>Allowed data: <span className="text-white">{profile.allowed_data_sources.join(", ") || "none"}</span></p>
                <p>Allowed actions: <span className="text-white">{profile.allowed_actions.join(", ") || "none"}</span></p>
                <p>Usage guardrail: <span className="text-white">{profile.max_llm_calls} calls · warn {profile.warning_threshold}% · critical {profile.critical_threshold}%</span></p>
              </div>
            ) : (
              <div className="mt-4">
                <p className="mb-2 text-xs text-rose-200">No behavior profile configured.</p>
                {!showProfileForm[agent.id] ? (
                  <div className="flex gap-2">
                    <button type="button" className="border border-white px-3 py-1 text-xs" onClick={() => setShowProfileForm((s) => ({ ...s, [agent.id]: true }))}>Add profile</button>
                    <button
                      type="button"
                      className="border border-rose-300 px-3 py-1 text-xs text-rose-200 hover:bg-rose-700/10"
                      onClick={() => setConfirmDelete(agent)}
                      disabled={deletingId === agent.id}
                    >
                      {deletingId === agent.id ? "Deleting…" : "Delete agent"}
                    </button>
                  </div>
                ) : (
                  <form className="mt-3 grid gap-2 sm:grid-cols-2" onSubmit={async (e) => {
                    e.preventDefault();
                    const values = profileForm[agent.id] || {};
                    const payload = {
                      agent_id: agent.id,
                      name: values.name || `${agent.name} profile`,
                      allowed_tools: (values.allowed_tools || "").split(",").map((s) => s.trim()).filter(Boolean),
                      allowed_data_sources: (values.allowed_data_sources || "").split(",").map((s) => s.trim()).filter(Boolean),
                      allowed_actions: (values.allowed_actions || "").split(",").map((s) => s.trim()).filter(Boolean),
                      max_llm_calls: Number(values.max_llm_calls || 1000),
                      warning_threshold: Number(values.warning_threshold || 80),
                      critical_threshold: Number(values.critical_threshold || 90),
                    };
                    try {
                      await onCreateProfile(payload);
                      setShowProfileForm((s) => ({ ...s, [agent.id]: false }));
                    } catch {
                      // error handled upstream
                    }
                  }}>
                    <label className="text-xs text-white/60">Profile name<input value={(profileForm[agent.id] || {}).name || ""} onChange={(ev) => setProfileForm((s) => ({ ...s, [agent.id]: { ...(s[agent.id] || {}), name: ev.target.value } }))} className="mt-1 w-full border border-white/25 bg-black px-2 py-1 text-sm outline-none" placeholder="Profile name" /></label>
                    <label className="text-xs text-white/60">Allowed tools<input value={(profileForm[agent.id] || {}).allowed_tools || ""} onChange={(ev) => setProfileForm((s) => ({ ...s, [agent.id]: { ...(s[agent.id] || {}), allowed_tools: ev.target.value } }))} className="mt-1 w-full border border-white/25 bg-black px-2 py-1 text-sm outline-none" placeholder="tool1,tool2" /></label>
                    <label className="text-xs text-white/60">Allowed data<input value={(profileForm[agent.id] || {}).allowed_data_sources || ""} onChange={(ev) => setProfileForm((s) => ({ ...s, [agent.id]: { ...(s[agent.id] || {}), allowed_data_sources: ev.target.value } }))} className="mt-1 w-full border border-white/25 bg-black px-2 py-1 text-sm outline-none" placeholder="source1,source2" /></label>
                    <label className="text-xs text-white/60">Allowed actions<input value={(profileForm[agent.id] || {}).allowed_actions || ""} onChange={(ev) => setProfileForm((s) => ({ ...s, [agent.id]: { ...(s[agent.id] || {}), allowed_actions: ev.target.value } }))} className="mt-1 w-full border border-white/25 bg-black px-2 py-1 text-sm outline-none" placeholder="action1,action2" /></label>
                    <label className="text-xs text-white/60">Max LLM calls<input type="number" value={(profileForm[agent.id] || {}).max_llm_calls || 1000} onChange={(ev) => setProfileForm((s) => ({ ...s, [agent.id]: { ...(s[agent.id] || {}), max_llm_calls: ev.target.value } }))} className="mt-1 w-full border border-white/25 bg-black px-2 py-1 text-sm outline-none" /></label>
                    <label className="text-xs text-white/60">Warning %<input type="number" value={(profileForm[agent.id] || {}).warning_threshold || 80} onChange={(ev) => setProfileForm((s) => ({ ...s, [agent.id]: { ...(s[agent.id] || {}), warning_threshold: ev.target.value } }))} className="mt-1 w-full border border-white/25 bg-black px-2 py-1 text-sm outline-none" /></label>
                    <label className="text-xs text-white/60">Critical %<input type="number" value={(profileForm[agent.id] || {}).critical_threshold || 90} onChange={(ev) => setProfileForm((s) => ({ ...s, [agent.id]: { ...(s[agent.id] || {}), critical_threshold: ev.target.value } }))} className="mt-1 w-full border border-white/25 bg-black px-2 py-1 text-sm outline-none" /></label>
                    <div className="flex items-end gap-2">
                      <button className="bg-white px-3 py-1 text-xs text-black">Save profile</button>
                      <button type="button" className="border px-3 py-1 text-xs" onClick={() => setShowProfileForm((s) => ({ ...s, [agent.id]: false }))}>Cancel</button>
                    </div>
                  </form>
                )}
              </div>
            )}
            <div className="mt-3">
              {profile && (
                  <button
                    type="button"
                    className="border border-rose-300 px-3 py-1 text-xs text-rose-200 hover:bg-rose-700/10"
                    onClick={() => setConfirmDelete(agent)}
                    disabled={deletingId === agent.id}
                  >
                    {deletingId === agent.id ? "Deleting…" : "Delete agent"}
                  </button>
              )}
              <div className="ml-2 text-xs text-white/60">Simulations must be run via an external environment agent.</div>
            </div>

          </article>

          );
        })}

      </div>

      {confirmDelete && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
          <div className="w-full max-w-lg rounded border border-white/20 bg-white/5 p-6">
            <h3 className="text-lg font-medium">Delete agent</h3>
            <p className="mt-3 text-sm text-white/60">Are you sure you want to permanently delete <strong className="text-white">{confirmDelete.name}</strong>? This cannot be undone.</p>
            <div className="mt-5 flex items-center gap-3">
              <button
                className="bg-rose-600 px-4 py-2 text-sm font-medium text-white hover:bg-rose-500 disabled:opacity-60"
                onClick={async () => {
                  setDeleteError("");
                  setDeletingId(confirmDelete.id);
                  try {
                    await onDeleteAgent(confirmDelete.id);
                    setConfirmDelete(null);
                  } catch (err) {
                    setDeleteError(err?.message || "Failed to delete agent");
                  } finally {
                    setDeletingId(null);
                  }
                }}
                disabled={deletingId === confirmDelete.id}
              >
                {deletingId === confirmDelete.id ? "Deleting…" : "Yes, delete"}
              </button>

              <button
                className="border px-4 py-2 text-sm"
                onClick={() => setConfirmDelete(null)}
                disabled={deletingId === confirmDelete.id}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

    </section>
  );
}
