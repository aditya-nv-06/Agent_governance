import { useState } from "react";
import { simulateAgent } from "../services/api";

export default function Agents({
  agents,
  profiles,
  onCreateAgent,
  onDeleteAgent,
  onCreateProfile,
  onSimulate,
}) {
  const [showCreate, setShowCreate] = useState(false);
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

  function parseList(value) {
    return (value || "").split(",").map((item) => item.trim()).filter(Boolean);
  }

  async function createAgent(event) {
    event.preventDefault();
    if (!name.trim()) return;

    const nextProfile = {
      name: profileName.trim() || `${name.trim()} profile`,
      allowed_tools: parseList(allowedTools),
      allowed_data_sources: parseList(allowedData),
      allowed_actions: parseList(allowedActions),
      max_llm_calls: Number(maxLlmCalls || 1000),
      warning_threshold: Number(warningThreshold || 80),
      critical_threshold: Number(criticalThreshold || 90),
    };

    try {
      setError("");
      await onCreateAgent({
        name: name.trim(),
        description: description.trim() || null,
        profile: nextProfile,
      });
      setName("");
      setDescription("");
      setProfileName("");
      setAllowedTools("");
      setAllowedData("");
      setAllowedActions("");
      setMaxLlmCalls("1000");
      setWarningThreshold("80");
      setCriticalThreshold("90");
      setShowCreate(false);
    } catch {
      setError("Agent creation requires a valid behavior profile. Please add a profile before saving the agent.");
    }
  }

  return (

    <section>

      <div className="mb-4 flex items-center justify-between gap-4">
        <div><h2 className="text-lg font-medium">Agents</h2><p className="mt-1 text-sm text-white/50">Create and monitor agents governed by policy.</p></div>
        <button type="button" className="border border-white px-3 py-2 text-xs font-medium hover:bg-white hover:text-black" onClick={() => setShowCreate((value) => !value)}>{showCreate ? "Cancel" : "Create agent"}</button>
      </div>

      {showCreate && (
        <form onSubmit={createAgent} className="mb-4 grid gap-3 border border-white/20 bg-white/[0.03] p-5 sm:grid-cols-2 sm:items-end">
          <label className="text-xs text-white/60">Agent name<input required value={name} onChange={(event) => setName(event.target.value)} className="mt-2 w-full border border-white/25 bg-black px-3 py-2 text-sm text-white outline-none focus:border-white" placeholder="e.g. Support Agent" /></label>
          <label className="text-xs text-white/60">Description<input value={description} onChange={(event) => setDescription(event.target.value)} className="mt-2 w-full border border-white/25 bg-black px-3 py-2 text-sm text-white outline-none focus:border-white" placeholder="What does this agent do?" /></label>

          <label className="text-xs text-white/60 sm:col-span-2">Behavior profile name<input required value={profileName} onChange={(event) => setProfileName(event.target.value)} className="mt-2 w-full border border-white/25 bg-black px-3 py-2 text-sm text-white outline-none focus:border-white" placeholder="Support profile" /></label>
          <label className="text-xs text-white/60">Allowed tools<input value={allowedTools} onChange={(event) => setAllowedTools(event.target.value)} className="mt-2 w-full border border-white/25 bg-black px-3 py-2 text-sm text-white outline-none focus:border-white" placeholder="tool_a, tool_b" /></label>
          <label className="text-xs text-white/60">Allowed data sources<input value={allowedData} onChange={(event) => setAllowedData(event.target.value)} className="mt-2 w-full border border-white/25 bg-black px-3 py-2 text-sm text-white outline-none focus:border-white" placeholder="source_a, source_b" /></label>
          <label className="text-xs text-white/60">Allowed actions<input value={allowedActions} onChange={(event) => setAllowedActions(event.target.value)} className="mt-2 w-full border border-white/25 bg-black px-3 py-2 text-sm text-white outline-none focus:border-white" placeholder="read, send_email" /></label>
          <label className="text-xs text-white/60">Max LLM calls<input type="number" min="1" value={maxLlmCalls} onChange={(event) => setMaxLlmCalls(event.target.value)} className="mt-2 w-full border border-white/25 bg-black px-3 py-2 text-sm text-white outline-none focus:border-white" /></label>
          <label className="text-xs text-white/60">Warning threshold %<input type="number" min="1" max="100" value={warningThreshold} onChange={(event) => setWarningThreshold(event.target.value)} className="mt-2 w-full border border-white/25 bg-black px-3 py-2 text-sm text-white outline-none focus:border-white" /></label>
          <label className="text-xs text-white/60">Critical threshold %<input type="number" min="1" max="100" value={criticalThreshold} onChange={(event) => setCriticalThreshold(event.target.value)} className="mt-2 w-full border border-white/25 bg-black px-3 py-2 text-sm text-white outline-none focus:border-white" /></label>

          <button type="submit" className="bg-white px-4 py-2 text-xs font-medium text-black hover:bg-white/80 sm:col-span-2">Create agent</button>
          {error && <p className="text-xs text-rose-200 sm:col-span-2">{error}</p>}
        </form>
      )}


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
              <button
                type="button"
                className="ml-2 border px-3 py-1 text-xs"
                onClick={async () => {
                  setSimLoadingId(agent.id);
                  setSimResult(null);
                  try {
                    await simulateAgent(agent.id, 5);
                    setSimResult({ message: "Simulation created" });
                    await onSimulate?.();
                  } catch (err) {
                    setSimResult({ error: err?.message || "Simulation failed" });
                  } finally {
                    setSimLoadingId(null);
                    setTimeout(() => setSimResult(null), 3000);
                  }
                }}
                disabled={simLoadingId === agent.id}
              >
                {simLoadingId === agent.id ? "Simulating…" : "Simulate"}
              </button>
              {simResult && simResult.error && <div className="mt-2 text-xs text-rose-200">{simResult.error}</div>}
              {simResult && simResult.message && <div className="mt-2 text-xs text-white/60">{simResult.message}</div>}
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
