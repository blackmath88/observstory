import { ClockIcon } from "@primer/octicons-react";
import { Link } from "@tanstack/react-router";
import type { EventSchedule, SourceResult } from "../../data/types";
import { useNow } from "../../lib/useNow";
import { eventClock } from "../../view/clock";
import { duration, zoned, zoneShort } from "../../view/time";

const PRECISION: Record<string, string> = { approximate: "approx.", after: "after", day_boundary_assumed: "day boundary assumed" };

/** Hands-off and the programme around now. The clock moves; the repository data does not. */
export function EventClock({ result }: { result: SourceResult<EventSchedule> }) {
  const now = useNow(30_000);
  if (result.status !== "ok") {
    return (
      <section className="box" aria-labelledby="clock-h">
        <div className="box-header">
          <ClockIcon size={16} />
          <h2 id="clock-h">Event clock</h2>
        </div>
        <div className="box-blank">
          {result.status === "missing" ? (
            "No event schedule is published."
          ) : (
            <>
              The event schedule could not be read. <Link to="/sources">See Data sources</Link>.
            </>
          )}
        </div>
      </section>
    );
  }
  const s = result.data;
  const c = eventClock(s, now);
  const tz = zoneShort(s.timezone, now);
  return (
    <section className="box" aria-labelledby="clock-h">
      <div className="box-header">
        <ClockIcon size={16} />
        <h2 id="clock-h">Event clock</h2>
        <span className="end">{tz}</span>
      </div>
      {c.deadline ? (
        <div className="box-row">
          <div className="main">
            <div className="eyebrow">{c.deadline.label}</div>
            <div className="countdown" aria-live="polite">
              {c.deadline.arrived ? "has arrived" : <>in {duration(c.deadline.remainingMs)}</>}
            </div>
            <div className="meta">
              {zoned(c.deadline.at, s.timezone)} {tz}
              {c.deadline.arrived && " · nothing is marked done by the clock"}
            </div>
          </div>
        </div>
      ) : (
        <div className="box-row">
          <div className="main meta">No coding deadline in this schedule.</div>
        </div>
      )}
      {c.current && (
        <div className="box-row compact">
          <span className="when">now</span>
          <div className="main">{c.current.label}</div>
        </div>
      )}
      {c.upcoming.map((e) => (
        <div className="box-row compact" key={e.id}>
          <span className="when mono">{zoned(e.start_at, s.timezone)}</span>
          <div className="main">
            {e.label}
            {e.precision && PRECISION[e.precision] && <span className="meta"> · {PRECISION[e.precision]}</span>}
          </div>
        </div>
      ))}
      <div className="box-footer">
        {s.source?.independently_verified === false
          ? "From the supplied timetable, not independently verified."
          : "From the published event schedule."}{" "}
        The countdown uses this device's clock; snapshot age is shown separately.
      </div>
    </section>
  );
}
