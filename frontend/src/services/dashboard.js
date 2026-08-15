import {
  getAgents,
  getApprovals,
  getAuditEvents,
  getFindings,
  getProfiles,
  getRuns,
} from "./api";


export async function getDashboardData() {
  const [agents, profiles, findings, approvals, runs, auditEvents] = await Promise.all([
    getAgents(),
    getProfiles(),
    getFindings(),
    getApprovals(),
    getRuns(),
    getAuditEvents(),
  ]);

  return { agents, profiles, findings, approvals, runs, auditEvents };
}
