const API_URL = (import.meta.env.VITE_API_URL || "/api").replace(/\/$/, "");


async function request(
  endpoint,
  options = {}
) {

  const response = await fetch(
    `${API_URL}${endpoint}`,
    {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
    }
  );


  if (!response.ok) {

    const error =
      await response.text();

    throw new Error(error);
  }


  return response.json();
}


// Agents
export function getAgents() {

  return request("/agents");
}

export function getProfiles() {
  return request("/profiles");
}


// Findings
export function getFindings() {

  return request("/findings");
}


// Approvals
export function getApprovals() {

  return request("/approvals");
}

export function decideApproval(approvalId, decision) {
  return request(`/approvals/${approvalId}/decision`, {
    method: "POST",
    body: JSON.stringify(decision),
  });
}

export function executeApprovedAction(approvalId) {
  return request(`/approvals/${approvalId}/execute`, { method: "POST" });
}


// Runs
export function getRuns() {

  return request("/runs");
}


// Audit
export function getAuditEvents() {

  return request("/audit");
}


// Execute Agent
export function runAgent(
  agentId,
  message
) {

  return request(
    "/runs",
    {
      method: "POST",

      body: JSON.stringify({
        agent_id: agentId,
        message: message,
      }),
    }
  );
}
