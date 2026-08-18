import { useState, useEffect } from "react";
import {
  connectToCustomerService,
  simulateCustomerScenario,
  getCustomerServiceHealth,
  getActiveCustomerServiceUrl,
} from "../services/api";

export default function CustomerService({ onSimulateComplete }) {
  const [serviceUrl, setServiceUrl] = useState(() => getActiveCustomerServiceUrl());
  const [customerId, setCustomerId] = useState("");
  const [scenarioType, setScenarioType] = useState("random");
  const [requestDescription, setRequestDescription] = useState("");
  const [seriesCount, setSeriesCount] = useState(5);
  const [isConnected, setIsConnected] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [health, setHealth] = useState(null);
  const [expandedSteps, setExpandedSteps] = useState({});

  const [statusMessage, setStatusMessage] = useState("");

  // Check connection on mount
  useEffect(() => {
    checkHealth(serviceUrl);
  }, []);

  async function checkHealth(urlToCheck = serviceUrl) {
    try {
      const healthStatus = await getCustomerServiceHealth(urlToCheck);
      setHealth(healthStatus);
      setIsConnected(true);
    } catch (err) {
      setHealth(null);
      setIsConnected(false);
    }
  }

  async function handleConnect(e) {
    if (e) e.preventDefault();
    setLoading(true);
    setError("");
    setStatusMessage("");
    try {
      const response = await connectToCustomerService(serviceUrl);
      setIsConnected(true);
      await checkHealth(serviceUrl);
      await onSimulateComplete?.(response);
      setStatusMessage(`✓ Connected & registered agent at ${serviceUrl}. The agent is now active and governed in the control room.`);
    } catch (err) {
      setError(err.message);
      setIsConnected(false);
    } finally {
      setLoading(false);
    }
  }

  async function handleSimulate(forcedType = null) {
    setLoading(true);
    setError("");
    setStatusMessage("");
    try {
      const typeToRun = forcedType || scenarioType || "random";
      const response = await simulateCustomerScenario(
        typeToRun,
        customerId || undefined,
        requestDescription || undefined,
        serviceUrl,
        Number(seriesCount) || 5
      );
      await onSimulateComplete?.(response);
      setStatusMessage(
        `✓ Simulation of ${response.total_requests || seriesCount} customer requests completed successfully (${response.approved_count || 0} approved, ${response.blocked_count || 0} blocked). Audit trails, security findings, and pending approvals have been dispatched to their respective dashboard sections below.`
      );
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function handleRandomizeFields() {
    const randomId = `CUST-${Math.floor(100 + Math.random() * 900)}`;
    setCustomerId(randomId);
    setScenarioType("random");
    setRequestDescription("");
  }

  return (
    <section className="border border-white/20 p-6 space-y-6">
      <div>
        <h2 className="text-lg font-medium">Customer Service Agent</h2>
        <p className="mt-1 text-sm text-white/50">
          Connect and govern external agent backends by URL. Simulated requests are continuously audited, and deviations generate security findings.
        </p>
      </div>

      {/* Health / Connection Status */}
      <div className="border border-white/20 p-4 rounded">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm font-medium">Service Status</div>
            <div className="text-xs text-white/60 mt-1">
              {isConnected
                ? `Connected to Customer Service Backend (${serviceUrl})`
                : `Disconnected from Customer Service Backend (${serviceUrl})`}
            </div>
          </div>
          <div
            className={`w-3 h-3 rounded-full ${isConnected ? "bg-green-500" : "bg-red-500"}`}
          />
        </div>
        {health && (
          <div className="mt-2 text-xs text-white/60 flex flex-wrap gap-4">
            <div>Environment: <span className="text-white">{health.environment}</span></div>
            <div>Port: <span className="text-white">{health.port || 8001}</span></div>
            <div>Service: <span className="text-white">{health.service || "Customer Service Agent"}</span></div>
          </div>
        )}
      </div>

      {/* URL Connection Section */}
      <div className="border border-white/20 p-4 rounded">
        <h3 className="text-sm font-medium mb-3">Backend Connection (URL)</h3>
        <form onSubmit={handleConnect} className="space-y-3">
          <div>
            <label className="text-xs text-white/60">Agent Backend URL</label>
            <div className="mt-1 flex gap-2">
              <input
                type="text"
                value={serviceUrl}
                onChange={(e) => setServiceUrl(e.target.value)}
                placeholder="http://localhost:8001"
                className="flex-1 rounded-sm border bg-black px-3 py-1.5 text-sm font-mono text-white"
              />
              <button
                type="submit"
                disabled={loading}
                className="bg-white px-4 py-1.5 text-sm text-black font-medium hover:bg-white/90 disabled:opacity-50"
              >
                {loading ? "Connecting..." : "Connect / Register"}
              </button>
            </div>
            <p className="mt-1 text-xs text-white/40">
              Direct connection via endpoint URL (no client ID/secret required). Registers the agent into governance.
            </p>
          </div>
        </form>
      </div>

      {/* Simulation Section */}
      <div className="border border-white/20 p-4 rounded">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h3 className="text-sm font-medium">Simulate Series of Customer Requests</h3>
            <p className="text-xs text-white/50">Run a multi-request session containing sequential actions with individual audit trails, findings, and approvals</p>
          </div>
          <button
            type="button"
            onClick={handleRandomizeFields}
            className="text-xs text-white/70 hover:text-white underline underline-offset-2"
          >
            🎲 Randomize inputs
          </button>
        </div>

        <div className="space-y-3">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-white/60">Scenario Type</label>
              <select
                value={scenarioType}
                onChange={(e) => setScenarioType(e.target.value)}
                className="w-full mt-1 rounded-sm border bg-black px-2 py-1.5 text-sm text-white"
              >
                <option value="random">🎲 Random Series (Dynamic Mix of Low-Risk & High-Risk)</option>
                <option value="auto_approval">✓ Auto Approval Series (Low-Risk Actions: Refunds, Replacements, Support)</option>
                <option value="blocked_approval">✗ Blocked Approval Series (High-Risk Actions: Suspensions, Exports, Large Refunds)</option>
              </select>
            </div>

            <div>
              <label className="text-xs text-white/60">Series Length (Number of Requests)</label>
              <select
                value={seriesCount}
                onChange={(e) => setSeriesCount(Number(e.target.value))}
                className="w-full mt-1 rounded-sm border bg-black px-2 py-1.5 text-sm text-white"
              >
                <option value={3}>3 sequential customer requests</option>
                <option value={5}>5 sequential customer requests (Standard Session)</option>
                <option value={8}>8 sequential customer requests</option>
                <option value={10}>10 sequential customer requests (Heavy Load)</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-white/60">Customer ID (optional)</label>
              <input
                type="text"
                value={customerId}
                onChange={(e) => setCustomerId(e.target.value)}
                placeholder="Leave blank for random (e.g. CUST-582)"
                className="w-full mt-1 rounded-sm border bg-black px-2 py-1.5 text-sm font-mono text-white"
              />
            </div>
            <div>
              <label className="text-xs text-white/60">Initial Request Context (optional)</label>
              <input
                type="text"
                value={requestDescription}
                onChange={(e) => setRequestDescription(e.target.value)}
                placeholder="Leave blank for auto-generated context"
                className="w-full mt-1 rounded-sm border bg-black px-2 py-1.5 text-sm text-white"
              />
            </div>
          </div>

          <div className="flex gap-2 pt-2">
            <button
              onClick={() => handleSimulate()}
              disabled={loading || !isConnected}
              className="flex-1 bg-white px-3 py-2 text-sm text-black font-medium hover:bg-white/90 disabled:opacity-50"
            >
              {loading ? "Simulating series..." : `Run Series (${seriesCount} Requests)`}
            </button>
            <button
              onClick={() => handleSimulate("random")}
              disabled={loading || !isConnected}
              className="border border-white/40 px-4 py-2 text-sm text-white hover:bg-white/10 disabled:opacity-50"
            >
              ⚡ Quick Random Series
            </button>
          </div>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="border border-red-500/50 bg-red-500/10 p-3.5 rounded text-sm text-red-400">
          {error}
        </div>
      )}

      {/* Status Banner */}
      {statusMessage && (
        <div className="border border-green-500/50 bg-green-500/10 p-3.5 rounded text-sm text-green-300 flex items-center justify-between">
          <span>{statusMessage}</span>
          <button
            type="button"
            onClick={() => setStatusMessage("")}
            className="text-xs text-green-400/70 hover:text-green-200 ml-3 underline"
          >
            Dismiss
          </button>
        </div>
      )}
    </section>
  );
}


