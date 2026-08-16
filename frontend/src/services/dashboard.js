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
  const [agents, profiles, findings, approvals, runs, auditEvents, analytics] = await Promise.all([
    getAgents(),
    getProfiles(),
    getFindings(),
    getApprovals(),
    getRuns(),
    getAuditEvents(),
    getAgentsAnalytics(),
  ]);

  return { agents, profiles, findings, approvals, runs, auditEvents, analytics };
}
