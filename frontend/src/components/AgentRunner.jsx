import { useState } from "react";

import {
  runAgent
} from "../services/api";


export default function AgentRunner({
  agentId,
  onComplete,
}) {

  const [message, setMessage] =
    useState("");

  const [result, setResult] =
    useState(null);

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState(null);


  async function handleRun() {

    if (!message.trim()) {
      return;
    }

    setLoading(true);

    setError(null);

    setResult(null);


    try {

      const data = await runAgent(
        agentId,
        message
      );

      setResult(data);
      await onComplete?.();

    } catch (error) {

      setError(
        error.message
      );

    } finally {

      setLoading(false);

    }
  }


  return (

    <section className="border border-white/20 p-6">

      <h2 className="text-lg font-medium">
        Run Agent
      </h2>

      <p className="mt-1 text-sm text-white/50">
        Enter a customer-support request. The agent proposes a tool; governance independently decides whether it may execute.
      </p>

      <p className="mt-2 text-xs text-white/40">
        Rule: approved profile scope → automatic execution. Outside scope → human approval required.
      </p>

      <div className="mt-4 grid gap-2 text-xs text-white/60 sm:grid-cols-2">
        <button type="button" onClick={() => setMessage("What is the refund policy?")} className="border border-white/15 p-3 text-left hover:border-white/50">
          <span className="block text-white">Allowed example</span>
          Refund policy → faq_search → execute
        </button>
        <button type="button" onClick={() => setMessage("Get customer information")} className="border border-white/15 p-3 text-left hover:border-white/50">
          <span className="block text-white">Approval example</span>
          Customer information → blocked → review
        </button>
      </div>


      <textarea
        value={message}
        onChange={(event) =>
          setMessage(
            event.target.value
          )
        }
        placeholder="Example: What is the refund policy?"
        className="mt-5 min-h-32 w-full border border-white/25 bg-black p-4 text-sm outline-none placeholder:text-white/30 focus:border-white"
      />


      <button
        onClick={handleRun}
        disabled={loading}
        className="mt-4 bg-white px-5 py-2.5 text-sm font-medium text-black hover:bg-white/80 disabled:cursor-not-allowed disabled:opacity-50"
      >

        {loading
          ? "Running..."
          : "Run Agent"}

      </button>


      {error && (

        <div className="mt-5 border border-white/30 p-4 text-sm">
          {error}
        </div>

      )}


      {result && (

        <div className="mt-5">

          <div className="border border-white/20 p-4 text-sm">
            <p className="font-medium">
              {result.status === "blocked" ? "Request blocked for review" : "Request completed"}
            </p>
            <p className="mt-1 text-white/60">
              Tool: <span className="text-white">{result.tool}</span> · Governance: <span className="text-white">{result.governance || result.status}</span>
            </p>
            {result.status === "blocked" && (
              <p className="mt-2 text-amber-100">Open Approvals below to approve or reject this request.</p>
            )}
          </div>

        </div>

      )}

    </section>
  );
}
