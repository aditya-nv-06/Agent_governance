import { useCallback, useEffect, useMemo, useState } from "react";

import AgentRunner from "./components/AgentRunner";
import Agents from "./components/Agents";
import Approvals from "./components/Approvals";
import AuditEvents from "./components/AuditEvents";
import Findings from "./components/Findings";
import Runs from "./components/Runs";
import Stats from "./components/Stats";
import { getDashboardData } from "./services/dashboard";
import { decideApproval, executeApprovedAction } from "./services/api";


const EMPTY_DASHBOARD = {
  agents: [],
  profiles: [],
  findings: [],
  approvals: [],
  runs: [],
  auditEvents: [],
};


function App() {
  const [dashboard, setDashboard] = useState(EMPTY_DASHBOARD);
  const [error, setError] = useState("");

  const loadDashboard = useCallback(async () => {
    try {
      setError("");
      setDashboard(await getDashboardData());
    } catch (requestError) {
      setError(requestError.message || "Unable to load dashboard data.");
    }
  }, []);

  useEffect(() => {
    let active = true;

    getDashboardData()
      .then((data) => {
        if (active) {
          setDashboard(data);
        }
      })
      .catch((requestError) => {
        if (active) {
          setError(requestError.message || "Unable to load dashboard data.");
        }
      });

    return () => {
      active = false;
    };
  }, []);

  const stats = useMemo(() => ({
    agents: dashboard.agents.length,
    activeRuns: dashboard.runs.filter((run) => run.status === "running").length,
    openFindings: dashboard.findings.filter((finding) => finding.status === "open" || !finding.status).length,
    pendingApprovals: dashboard.approvals.filter((approval) => approval.status === "PENDING").length,
  }), [dashboard]);

  async function handleApproval(approvalId, approved) {
    const decidedBy = window.prompt("Decision maker", "governance-admin");
    const reason = window.prompt("Decision reason");
    if (!decidedBy || !reason) return;

    try {
      await decideApproval(approvalId, { approved, decided_by: decidedBy, reason });
      await loadDashboard();
    } catch (requestError) {
      setError(requestError.message || "Unable to record decision.");
    }
  }

  async function handleApprovedExecution(approvalId) {
    try {
      await executeApprovedAction(approvalId);
      await loadDashboard();
    } catch (requestError) {
      setError(requestError.message || "Unable to execute approved action.");
    }
  }

  return (
    <main className="min-h-screen bg-black px-5 py-8 text-white sm:px-8">
      <div className="mx-auto max-w-6xl">
        <header className="mb-10 flex items-end justify-between border-b border-white/30 pb-5">
          <div>
            <p className="text-xs uppercase tracking-[0.25em] text-white/50">Control room</p>
            <h1 className="mt-2 text-3xl font-medium tracking-tight">Agent governance</h1>
          </div>
          <button className="text-sm text-white/70 underline underline-offset-4 hover:text-white" onClick={loadDashboard}>
            Refresh
          </button>
        </header>

        {error && <p className="mb-6 border border-white/30 p-4 text-sm">{error}</p>}

        <Stats {...stats} />

        <div className="mt-10 space-y-10">
          <Agents agents={dashboard.agents} profiles={dashboard.profiles} />
          {dashboard.agents[0] && <AgentRunner agentId={dashboard.agents[0].id} onComplete={loadDashboard} />}
          <Runs runs={dashboard.runs} />
          <Findings findings={dashboard.findings} />
          <Approvals
            approvals={dashboard.approvals}
            onDecision={handleApproval}
            onExecute={handleApprovedExecution}
          />
          <AuditEvents events={dashboard.auditEvents} />
        </div>
      </div>
    </main>
  );
}


export default App;
