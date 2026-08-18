function getApiBaseUrl() {
  const configured = import.meta.env.VITE_API_URL?.trim();
  if (configured) {
    return configured.replace(/\/$/, "");
  }

  const hostname = typeof window !== "undefined" ? window.location.hostname : "";
  if (hostname === "localhost" || hostname === "127.0.0.1") {
    return "/api";
  }

  throw new Error("Missing VITE_API_URL. Set it to https://agent-governance-dgg5.onrender.com and redeploy the frontend.");
}

function getCustomerServiceUrl() {
  const configured = import.meta.env.VITE_CUSTOMER_SERVICE_URL?.trim();
  if (configured) {
    return configured.replace(/\/$/, "");
  }

  const hostname = typeof window !== "undefined" ? window.location.hostname : "";
  if (hostname === "localhost" || hostname === "127.0.0.1") {
    return "http://localhost:8001/api";
  }

  return null; // Not configured
}

const API_URL = getApiBaseUrl();
const CUSTOMER_SERVICE_URL = getCustomerServiceUrl();
const ACTIVE_SESSION_KEY = "agent-governance-active-admin";
// Base key for storing sessions. Per-admin sessions are stored as "agent-governance-admin:<id>".
const SESSION_KEY_PREFIX = "agent-governance-admin";

function getSessionKey(adminId) {
  return adminId ? `${SESSION_KEY_PREFIX}:${adminId}` : SESSION_KEY_PREFIX;
}

export function getSession() {
  const activeAdminId = localStorage.getItem(ACTIVE_SESSION_KEY);
  const activeKey = activeAdminId ? getSessionKey(activeAdminId) : null;

  try {
    if (activeKey) {
      const activeSession = JSON.parse(localStorage.getItem(activeKey) || "null");
      if (activeSession) {
        return activeSession;
      }
    }

    const legacySession = JSON.parse(localStorage.getItem(SESSION_KEY_PREFIX) || "null");
    return legacySession;
  } catch {
    return null;
  }
}

export function saveSession(session) {
  const adminId = session?.admin?.id;
  if (adminId) {
    localStorage.setItem(getSessionKey(adminId), JSON.stringify(session));
    localStorage.setItem(ACTIVE_SESSION_KEY, adminId);
    return;
  }

  localStorage.setItem(SESSION_KEY_PREFIX, JSON.stringify(session));
  localStorage.setItem(ACTIVE_SESSION_KEY, "legacy");
}

export function clearSession() {
  const perAdminPrefix = `${SESSION_KEY_PREFIX}:`;
  const keys = Object.keys(localStorage).filter((key) => key.startsWith(perAdminPrefix) || key === SESSION_KEY_PREFIX);
  keys.forEach((key) => localStorage.removeItem(key));
  localStorage.removeItem(ACTIVE_SESSION_KEY);
}


async function request(
  endpoint,
  options = {}
) {
  try {
    const response = await fetch(
      `${API_URL}${endpoint}`,
      {
        ...options,
        headers: {
          "Content-Type": "application/json",
          ...(getSession()?.access_token ? { Authorization: `Bearer ${getSession().access_token}` } : {}),
          ...options.headers,
        },
      }
    );

    if (!response.ok) {
      const payload = await response.json().catch(() => null);
      const error = payload?.detail || "Request failed. Please try again.";
      throw new Error(error);
    }

    if (response.status === 204) return null;
    return response.json();
  } catch (error) {
    if (error instanceof TypeError) {
      throw new Error("Unable to reach the backend. Check that the backend is running and VITE_API_URL is configured correctly.");
    }
    throw error;
  }
}

export function registerAdmin(payload) {
  return request("/auth/register", { method: "POST", body: JSON.stringify(payload) });
}

export function loginAdmin(payload) {
  return request("/auth/login", { method: "POST", body: JSON.stringify(payload) });
}


// Agents
export function getAgents() {

  return request("/agents");
}

export function createAgent(payload) {
  return request("/agents", { method: "POST", body: JSON.stringify(payload) });
}

export function deleteAgent(agentId) {
  return request(`/agents/${agentId}`, { method: "DELETE" });
}

export function getProfiles() {
  return request("/profiles");
}

export function createProfile(payload) {
  return request(`/profiles`, { method: "POST", body: JSON.stringify(payload) });
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

// Simulation and analytics
export function simulateAgent(agentId, count = 5) {
  return request(`/simulate/${agentId}?count=${count}`, { method: "POST" });
}

export function getAgentsAnalytics() {
  return request(`/simulate/analytics/agents`);
}

// Environment agents (external URL-driven agents)
export function registerEnvAgent(payload) {
  return request(`/env/agents`, { method: "POST", body: JSON.stringify(payload) });
}

export function getEnvAgents() {
  return request(`/env/agents`);
}

export function triggerEnvAgent(agentId, payload) {
  return request(`/env/agents/${agentId}/trigger`, { method: "POST", body: JSON.stringify(payload) });
}

export function getEnvLogs(agentId) {
  return request(`/env/logs${agentId ? `?agent_id=${agentId}` : ""}`);
}

// Customer Service Backend - Second Backend for Governance Testing
const CS_URL_STORAGE_KEY = "agent-governance-cs-url";

export function getActiveCustomerServiceUrl() {
  const stored = typeof localStorage !== "undefined" ? localStorage.getItem(CS_URL_STORAGE_KEY)?.trim() : null;
  if (stored) {
    let clean = stored.replace(/\/$/, "");
    if (!clean.endsWith("/api")) {
      clean = `${clean}/api`;
    }
    return clean;
  }

  const defaultUrl = getCustomerServiceUrl();
  if (defaultUrl) {
    return defaultUrl;
  }

  return "http://localhost:8001/api";
}

export function setActiveCustomerServiceUrl(url) {
  if (typeof localStorage === "undefined") return;
  if (!url) {
    localStorage.removeItem(CS_URL_STORAGE_KEY);
    return;
  }
  let clean = url.trim().replace(/\/$/, "");
  localStorage.setItem(CS_URL_STORAGE_KEY, clean);
}

async function customerServiceRequest(
  endpoint,
  options = {},
  overrideUrl = null
) {
  let baseUrl = overrideUrl ? overrideUrl.trim().replace(/\/$/, "") : getActiveCustomerServiceUrl();
  if (!baseUrl.endsWith("/api")) {
    baseUrl = `${baseUrl}/api`;
  }

  try {
    const response = await fetch(
      `${baseUrl}${endpoint}`,
      {
        ...options,
        headers: {
          "Content-Type": "application/json",
          ...options.headers,
        },
      }
    );

    if (!response.ok) {
      const payload = await response.json().catch(() => null);
      const error = payload?.detail || `Request failed with status ${response.status}`;
      throw new Error(error);
    }

    if (response.status === 204) return null;
    return response.json();
  } catch (error) {
    if (error instanceof TypeError) {
      throw new Error(`Unable to reach Customer Service Backend at ${baseUrl}. Check that the service is running and accessible.`);
    }
    throw error;
  }
}

// Customer Service Endpoints - Connect using URL
export async function connectToCustomerService(serviceUrl) {
  const urlToTest = serviceUrl?.trim() || getActiveCustomerServiceUrl();
  const response = await customerServiceRequest("/connect", {
    method: "POST",
    body: JSON.stringify({
      url: urlToTest,
      service_name: "Customer Service Agent",
    }),
  }, urlToTest);

  // Synchronize with primary governance platform
  try {
    await request("/external/agents/connect", {
      method: "POST",
      body: JSON.stringify({
        url: urlToTest,
        name: "Customer Service Agent",
        purpose: "Customer Service Automation & Support",
      }),
    });
  } catch (err) {
    console.warn("Could not register external agent on governance platform:", err);
  }

  setActiveCustomerServiceUrl(urlToTest);
  return response;
}

export function simulateCustomerScenario(scenarioType = "random", customerId = null, requestDescription = null, customUrl = null, seriesCount = 5) {
  return customerServiceRequest("/simulate", {
    method: "POST",
    body: JSON.stringify({
      scenario_type: scenarioType || "random",
      customer_id: customerId || undefined,
      request_description: requestDescription || undefined,
      series_count: seriesCount || 5,
    }),
  }, customUrl);
}

export function getCustomerServiceDocs(customUrl = null) {
  return customerServiceRequest("/docs/api", {}, customUrl);
}

export function getCustomerServiceFlows(customUrl = null) {
  return customerServiceRequest("/docs/flows", {}, customUrl);
}

export function getCustomerServiceHealth(customUrl = null) {
  return customerServiceRequest("/connect/health", {}, customUrl);
}

