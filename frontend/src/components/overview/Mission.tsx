import { MilestoneIcon } from "@primer/octicons-react";
import type { Coordination } from "../../data/types";
import { type MissionItem, mission } from "../../view/mission";
import { zoned } from "../../view/time";

/** Declared sessions and gates on one axis, with every label written out in full below it. */
export function Mission({
  coordination,
  timezone,
  now,
}: {
  coordination: Coordination | null | undefined;
  timezone: string | undefined;
  now: Date;
}) {
  const m = mission(coordination, now);
  const when = (iso: string) =>
    timezone ? zoned(iso, timezone) : new Date(iso).toLocaleString(undefined, { weekday: "short", hour: "2-digit", minute: "2-digit" });
  if (!m) {
    return (
      <section className="box" aria-labelledby="mission-h">
        <div className="box-header">
          <MilestoneIcon size={16} />
          <h2 id="mission-h">Mission</h2>
        </div>
        <div className="box-row">
          <div className="main meta">
            Nothing declared yet. Sessions, gates and commitments come from <code>.observstory/coordination.json</code>.
          </div>
        </div>
      </section>
    );
  }
  const times = m.items.map((i) => Date.parse(i.at)).concat(now.getTime());
  const t0 = Math.min(...times);
  const t1 = Math.max(...times);
  const pos = (t: number) => (t1 > t0 ? ((t - t0) / (t1 - t0)) * 100 : 50);
  return (
    <section className="box" aria-labelledby="mission-h">
      <div className="box-header">
        <MilestoneIcon size={16} />
        <h2 id="mission-h">Mission</h2>
        <span className="label">declared</span>
        <span className="end">
          {m.proposedPending > 0 && (
            <span title="Proposed items are never shown as commitments until a person confirms them">
              {m.proposedPending} proposed item{m.proposedPending > 1 ? "s" : ""} await confirmation ·{" "}
              <code>observstory checkin pending</code>
            </span>
          )}
        </span>
      </div>
      <div className="box-row">
        <div className="main">
          <div className="mission-next">
            {m.next ? (
              <>
                Next: <strong>{m.next.label}</strong> · {when(m.next.at)}
                {Date.parse(m.next.at) > now.getTime() && (
                  <span className="meta"> · in {formatHours((Date.parse(m.next.at) - now.getTime()) / 3.6e6)}</span>
                )}
              </>
            ) : m.confirmedCheckpoints === 0 ? (
              <strong>No confirmed checkpoints yet.</strong>
            ) : (
              <strong>No upcoming checkpoint.</strong>
            )}
          </div>
          <div className="axis" aria-hidden="true">
            <div className="axis-line" />
            <div className="axis-past" style={{ width: `${pos(now.getTime())}%` }} />
            {m.items.map((i) => (
              <span key={i.id} className={`axis-mark ${markClass(i)}`} style={{ left: `${pos(Date.parse(i.at))}%` }} title={i.label} />
            ))}
            <span className="axis-now" style={{ left: `${pos(now.getTime())}%` }}>
              <span>NOW</span>
            </span>
          </div>
        </div>
      </div>
      <ol className="timeline">
        {m.items.map((i, k) => (
          <MissionRow key={i.id} item={i} when={when(i.at)} showNow={k === m.nowIndex} nowLabel={when(now.toISOString())} />
        ))}
        {m.nowIndex === m.items.length && <NowRow label={when(now.toISOString())} />}
      </ol>
      <div className="box-footer">
        Declared by people in <code>.observstory/coordination.json</code>; each gate's state comes from the repository, not from the clock.
      </div>
    </section>
  );
}

function MissionRow({ item, when, showNow, nowLabel }: { item: MissionItem; when: string; showNow: boolean; nowLabel: string }) {
  return (
    <>
      {showNow && <NowRow label={nowLabel} />}
      <li className="timeline-row">
        <span className={`timeline-mark ${markClass(item)}`} aria-hidden="true" />
        <span className="when mono">{when}</span>
        <div className="main">
          <div>
            {item.label}{" "}
            {item.kind === "gate" && (
              <span className={`label${item.state === "next" ? " accent" : ""}`}>
                {item.state === "passed" ? "passed" : item.state === "next" ? "next gate" : "gate"}
              </span>
            )}
          </div>
          <div className="meta">
            {item.kind === "session" ? item.sub : `${item.sub}${item.confirmedBy ? ` · confirmed by ${item.confirmedBy}` : ""}`}
          </div>
          {item.kind === "session" && item.openQuestions.length > 0 && (
            <details className="meta">
              <summary>
                {item.openQuestions.length} open question{item.openQuestions.length > 1 ? "s" : ""}
              </summary>
              <ul className="plain-list">
                {item.openQuestions.map((q) => (
                  <li key={q}>{q}</li>
                ))}
              </ul>
            </details>
          )}
        </div>
      </li>
    </>
  );
}

function NowRow({ label }: { label: string }) {
  return (
    <li className="timeline-row now">
      <span className="timeline-mark now" aria-hidden="true" />
      <span className="when mono">{label}</span>
      <div className="main">
        <strong>Now</strong>
      </div>
    </li>
  );
}

const markClass = (i: MissionItem) => (i.kind === "session" ? "session" : `gate ${i.state}`);
const formatHours = (h: number) => (h < 1 ? `${Math.round(h * 60)} min` : `${h.toFixed(h < 10 ? 1 : 0)} h`);
