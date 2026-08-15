export default function Findings({
  findings,
}) {

  return (

    <section>

      <h2 className="mb-4 text-lg font-medium">
        Security Findings
      </h2>


      <div className="space-y-3">

        {findings.map((finding) => (

          <div
            key={finding.id}
            className="border border-white/20 p-5"
          >

            <div className="flex justify-between">

              <h3 className="font-medium">
                {finding.finding_type}
              </h3>

              <span className="border border-white/25 px-3 py-1 text-xs uppercase tracking-wider text-white/70">
                {finding.severity}
              </span>

            </div>


            <p className="mt-2 text-sm text-white/50">
              {finding.reason}
            </p>


            <div className="mt-3 text-xs text-white/40">

              <p>
                Expected: {finding.expected}
              </p>

              <p>
                Actual: {finding.actual}
              </p>

            </div>

          </div>

        ))}

      </div>

    </section>
  );
}
