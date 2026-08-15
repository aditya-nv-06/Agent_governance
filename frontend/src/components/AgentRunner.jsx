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
        Test an agent request through the governance layer.
      </p>


      <textarea
        value={message}
        onChange={(event) =>
          setMessage(
            event.target.value
          )
        }
        placeholder="Ask the agent something..."
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

          <div className="mb-2 text-sm font-medium text-white/50">
            Execution Result
          </div>

          <pre className="overflow-auto border border-white/20 bg-black p-4 text-xs text-white/70">
            {JSON.stringify(
              result,
              null,
              2
            )}
          </pre>

        </div>

      )}

    </section>
  );
}
