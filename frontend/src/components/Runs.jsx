export default function Runs({
  runs,
}) {

  return (

    <section>

      <h2 className="mb-4 text-lg font-medium">
        Agent Runs
      </h2>


      <div className="space-y-3">

        {runs.map((run) => (

          <div
            key={run.id}
            className="flex items-center justify-between border border-white/20 p-5"
          >

            <div>

              <p className="font-medium">
                Agent Run
              </p>

              <p className="font-mono text-xs text-white/40">
                {run.id}
              </p>

            </div>


            <span className="border border-white/25 px-3 py-1 text-xs uppercase tracking-wider text-white/70">
              {run.status}
            </span>

          </div>

        ))}

      </div>

    </section>
  );
}
