import { useCallback, useEffect, useMemo, useState } from "react";

import AuthPage from "./components/AuthPage";
import Agents from "./components/Agents";
import CustomerService from "./components/CustomerService";
import Analytics from "./components/Analytics";
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

  // Merge simulation response payload (from CustomerService) into dashboard for immediate UI updates
  async function mergeSimulationResults(simResponse) {
    if (!simResponse) return loadDashboard();
    try {
      const data = await getDashboardData();

      // simulation returns a `series` array where each step includes `audit_events` and `findings`
      const series = Array.isArray(simResponse.series) ? simResponse.series : [];
      const simAudit = series.flatMap((s) => (Array.isArray(s.audit_events) ? s.audit_events : []));
      const simFindings = series.flatMap((s) => (Array.isArray(s.findings) ? s.findings : []));

      const mergedAudit = simAudit.length ? [...simAudit, ...(data.auditEvents || [])] : data.auditEvents;
      const mergedFindings = simFindings.length ? [...simFindings, ...(data.findings || [])] : data.findings;

      // For runs, try to extract any run ids from series steps
      const simRuns = series.flatMap((s) => (s.run_id ? [{ id: s.run_id, trace_id: s.trace_id, status: s.approval_status }] : []));
      const mergedRuns = simRuns.length ? [...simRuns, ...(data.runs || [])] : data.runs;

      // Ensure agent created via external connect or inferred from audit events is visible immediately
      let mergedAgents = data.agents || [];
      // Prefer explicit agent_id on the top-level response
      let inferredAgentId = simResponse.agent_id;
      let inferredAgentName = simResponse.name;

      if (!inferredAgentId && simAudit && simAudit.length) {
        const fromEvent = simAudit.find((e) => e && (e.agent_id || (e.details && e.details.agent_id)));
        if (fromEvent) {
          inferredAgentId = fromEvent.agent_id || (fromEvent.details && fromEvent.details.agent_id);
          inferredAgentName = inferredAgentName || (fromEvent.details && fromEvent.details.agent_name) || fromEvent.actor;
        }
      }

      if (inferredAgentId) {
        const exists = mergedAgents.find((a) => String(a.id) === String(inferredAgentId));
        if (!exists) {
          mergedAgents = [{ id: inferredAgentId, name: inferredAgentName || "External Agent", description: simResponse.url || "" }, ...mergedAgents];
        }
      }

      setDashboard({
        ...data,
        agents: mergedAgents,
        auditEvents: mergedAudit,
        findings: mergedFindings,
        runs: mergedRuns,
      });
    } catch (err) {
      await loadDashboard();
    }
  }

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
    openFindings: dashboard.findings.filter((finding) => String(finding.status).toLowerCase() === "open" || !finding.status).length,
    pendingApprovals: dashboard.approvals.filter((approval) => String(approval.status).toUpperCase() === "PENDING").length,
  }), [dashboard]);

  async function handleApproval(approvalId, decision) {
    const isApproved = Boolean(decision.approved);
    const nextStatus = isApproved ? "APPROVED" : "REJECTED";

    // 1. Instant Optimistic State Update for instantaneous count reduction
    setDashboard((prev) => {
      const targetApproval = prev.approvals.find((a) => String(a.id) === String(approvalId));
      const findingId = targetApproval?.finding_id;

      const nextApprovals = prev.approvals.map((a) =>
        String(a.id) === String(approvalId)
          ? {
              ...a,
              status: nextStatus,
              decided_by: decision.decided_by || "governance-admin",
              decision_reason: decision.reason,
            }
          : a
      );

      const nextFindings = findingId
        ? prev.findings.map((f) =>
            String(f.id) === String(findingId)
              ? { ...f, status: isApproved ? "approved" : "rejected" }
              : f
          )
        : prev.findings;

      return {
        ...prev,
        approvals: nextApprovals,
        findings: nextFindings,
      };
    });

    try {
      await decideApproval(approvalId, decision);
      // 2. Refresh authoritative dashboard data
      const data = await getDashboardData();
      setDashboard(data);
    } catch (requestError) {
      setError(requestError.message || "Unable to record decision.");
      await loadDashboard();
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
          
          <CustomerService onSimulateComplete={mergeSimulationResults} />
          <Analytics analytics={dashboard.analytics || []} />
          <Runs
            runs={dashboard.runs}
            agents={dashboard.agents}
            auditEvents={dashboard.auditEvents}
          />
          <Findings
            findings={dashboard.findings}
            agents={dashboard.agents}
            approvals={dashboard.approvals}
            onDecision={handleApproval}
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
