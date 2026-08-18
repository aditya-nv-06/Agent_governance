import {
  getAgents,
  getApprovals,
  getAuditEvents,
  getFindings,
  getProfiles,
  getRuns,
  getAgentsAnalytics,
} from "./api";


export async function getDashboardData() {
  const [agentsRes, profilesRes, findingsRes, approvalsRes, runsRes, auditEventsRes, analyticsRes] =
    await Promise.allSettled([
      getAgents(),
      getProfiles(),
      getFindings(),
      getApprovals(),
      getRuns(),
      getAuditEvents(),
      getAgentsAnalytics(),
    ]);

  return {
    agents: agentsRes.status === "fulfilled" && Array.isArray(agentsRes.value) ? agentsRes.value : [],
    profiles: profilesRes.status === "fulfilled" && Array.isArray(profilesRes.value) ? profilesRes.value : [],
    findings: findingsRes.status === "fulfilled" && Array.isArray(findingsRes.value) ? findingsRes.value : [],
    approvals: approvalsRes.status === "fulfilled" && Array.isArray(approvalsRes.value) ? approvalsRes.value : [],
    runs: runsRes.status === "fulfilled" && Array.isArray(runsRes.value) ? runsRes.value : [],
    auditEvents: auditEventsRes.status === "fulfilled" && Array.isArray(auditEventsRes.value) ? auditEventsRes.value : [],
    analytics: analyticsRes.status === "fulfilled" && analyticsRes.value ? analyticsRes.value : {},
  };
}
