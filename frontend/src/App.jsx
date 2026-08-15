import { useCallback, useEffect, useMemo, useState } from "react";

import AgentRunner from "./components/AgentRunner";
import AuthPage from "./components/AuthPage";
import Agents from "./components/Agents";
import Approvals from "./components/Approvals";
import AuditEvents from "./components/AuditEvents";
import Findings from "./components/Findings";
import Runs from "./components/Runs";
import Stats from "./components/Stats";
import { getDashboardData } from "./services/dashboard";
import { clearSession, createAgent, createProfile, deleteAgent, decideApproval, executeApprovedAction, getSession, loginAdmin, registerAdmin, saveSession } from "./services/api";


const EMPTY_DASHBOARD = {
  agents: [],
  profiles: [],
  findings: [],
  approvals: [],
  runs: [],
  auditEvents: [],
};


function App() {
  const [session, setSession] = useState(getSession);
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
    if (!session) return undefined;
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
  }, [session]);

  const stats = useMemo(() => ({
    agents: dashboard.agents.length,
    activeRuns: dashboard.runs.filter((run) => run.status === "running").length,
    openFindings: dashboard.findings.filter((finding) => finding.status === "open" || !finding.status).length,
    pendingApprovals: dashboard.approvals.filter((approval) => approval.status === "PENDING").length,
  }), [dashboard]);

  async function handleApproval(approvalId, decision) {
    try {
      await decideApproval(approvalId, decision);
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

  async function handleAuthentication(mode, credentials) {
    try {
      setError("");
      const nextSession = mode === "login" ? await loginAdmin(credentials) : await registerAdmin(credentials);
      saveSession(nextSession);
      setSession(nextSession);
    } catch (requestError) {
      setError(requestError.message || "Unable to authenticate.");
    }
  }

  async function handleCreateAgent(payload) {
    try {
      await createAgent(payload);
      await loadDashboard();
    } catch (requestError) {
      setError(requestError.message || "Unable to create agent.");
      throw requestError;
    }
  }

  async function handleDeleteAgent(agentId) {
    try {
      await deleteAgent(agentId);
      await loadDashboard();
    } catch (requestError) {
      setError(requestError.message || "Unable to delete agent.");
      throw requestError;
    }
  }

  async function handleCreateProfile(payload) {
    try {
      await createProfile(payload);
      await loadDashboard();
    } catch (requestError) {
      setError(requestError.message || "Unable to create profile.");
      throw requestError;
    }
  }

  if (!session) {
    return <AuthPage onAuthenticate={handleAuthentication} error={error} />;
  }

  return (
    <main className="min-h-screen bg-black px-5 py-8 text-white sm:px-8">
      <div className="mx-auto max-w-6xl">
        <header className="mb-10 flex items-end justify-between border-b border-white/30 pb-5">
          <div>
            <p className="text-xs uppercase tracking-[0.25em] text-white/50">Control room</p>
            <h1 className="mt-2 text-3xl font-medium tracking-tight">Agent governance</h1>
          </div>
          <div className="flex items-center gap-4 text-sm">
            <span className="hidden text-white/50 sm:inline">{session.admin.email}</span>
            <button className="text-white/70 underline underline-offset-4 hover:text-white" onClick={loadDashboard}>Refresh</button>
            <button className="text-white/70 underline underline-offset-4 hover:text-white" onClick={() => { clearSession(); setSession(null); setDashboard(EMPTY_DASHBOARD); }}>Sign out</button>
          </div>
        </header>

        {error && <p className="mb-6 border border-white/30 p-4 text-sm">{error}</p>}

        <Stats {...stats} />

        <div className="mt-10 space-y-10">
          <Agents agents={dashboard.agents} profiles={dashboard.profiles} onCreateAgent={handleCreateAgent} onDeleteAgent={handleDeleteAgent} onCreateProfile={handleCreateProfile} />
          {dashboard.agents[0] && <AgentRunner agentId={dashboard.agents[0].id} onComplete={loadDashboard} />}
          <Runs
            runs={dashboard.runs}
            agents={dashboard.agents}
            auditEvents={dashboard.auditEvents}
          />
          <Findings
            findings={dashboard.findings}
            agents={dashboard.agents}
            approvals={dashboard.approvals}
          />
          <Approvals
            approvals={dashboard.approvals}
            findings={dashboard.findings}
            runs={dashboard.runs}
            agents={dashboard.agents}
            onDecision={handleApproval}
            onExecute={handleApprovedExecution}
          />
          <AuditEvents
            events={dashboard.auditEvents}
            agents={dashboard.agents}
            findings={dashboard.findings}
          />
        </div>
      </div>
    </main>
  );
}


export default App;
