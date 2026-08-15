export default function AuditEvents({
  events,
}) {

  return (

    <section>

      <h2 className="mb-4 text-lg font-medium">
        Audit Events
      </h2>


      <div className="space-y-3">

        {events.map((event) => (

          <div
            key={event.id}
            className="border border-white/20 p-5"
          >

            <div className="flex items-center justify-between">

              <h3 className="font-medium">
                {event.event_type}
              </h3>

              <span className="text-xs uppercase tracking-wider text-white/50">
                {event.actor}
              </span>

            </div>


            <p className="mt-2 text-sm text-white/50">
              {JSON.stringify(event.details)}
            </p>

          </div>

        ))}

      </div>

    </section>
  );
}
