export default function Agents({
  agents,
  profiles,
}) {

  return (

    <section>

      <h2 className="mb-4 text-lg font-medium">
        Agents
      </h2>


      <div className="space-y-3">

        {agents.map((agent) => {
          const profile = profiles.find((item) => item.agent_id === agent.id);

          return (

          <div
            key={agent.id}
            className="flex items-center justify-between border border-white/20 p-5"
          >

            <div>

              <h3 className="font-medium">
                {agent.name}
              </h3>

              <p className="mt-1 text-sm text-white/50">
                {agent.description}
              </p>

              <p className="mt-3 text-xs uppercase tracking-wider text-white/40">
                {profile ? `Tools: ${profile.allowed_tools.join(", ") || "none"}` : "No behavior profile"}
              </p>

            </div>


            <span className="border border-white/25 px-3 py-1 text-xs uppercase tracking-wider text-white/70">
              {agent.status}
            </span>

          </div>

          );
        })}

      </div>

    </section>
  );
}
