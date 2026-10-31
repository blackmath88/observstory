import { AlertIcon, ClockIcon, GitPullRequestIcon, LinkIcon } from "@primer/octicons-react";
import { createFileRoute, getRouteApi, Link } from "@tanstack/react-router";
import { EventClock } from "../../components/overview/EventClock";
import { LaneBoard } from "../../components/overview/LaneBoard";
import { Mission } from "../../components/overview/Mission";
import { ProjectNow } from "../../components/overview/ProjectNow";
import { RemainingWork } from "../../components/overview/RemainingWork";
import { SourceStatus } from "../../components/SourceStatus";
import { absolute } from "../../data/freshness";
import { activity, SOURCES } from "../../data/load";
import type { SceneAttention, Snapshot } from "../../data/types";
import { useNow } from "../../lib/useNow";

export const Route = createFileRoute("/_app/")({ component: Overview });
const layout = getRouteApi("/_app");

/** Reading order from HACKATHON-PROJECT-VIEW.md: project now and time, the declared mission,
 *  then activity. Each panel degrades on its own when its input is missing. */
function Overview() {
  const bundle = layout.useLoaderData();
  const now = useNow(30_000);
  const act = activity(bundle);
  const timezone = bundle.event.status === "ok" ? bundle.event.data.timezone : undefined;
  return (
    <>
      <div className="page-grid">
        <ProjectNow result={bundle.knowledge} />
        <EventClock result={bundle.event} />
      </div>
      {!act ? (
        <div className="flash danger" role="alert">
          <AlertIcon size={16} />
          <div>
            <strong>Activity is unavailable.</strong>
            {typeof window !== "undefined" && window.location.protocol === "file:" ? (
              <p>
                This page was opened from a file, and browsers do not let it read the <code>data/</code> folder from disk. Open{" "}
                <a href="./map.html">the classic map</a>, which works offline, or serve this folder (for example{" "}
                <code>python3 -m http.server</code>) and open it from there.
              </p>
            ) : (
              <p>
                The snapshot and scene are both needed to show work in flight. Nothing is shown as zero.{" "}
                <Link to="/sources">See what went wrong in Data sources</Link>.
              </p>
            )}
          </div>
        </div>
      ) : (
        <>
          <Mission coordination={act.scene.coordination} timezone={timezone} now={now} />
          {act.snapshot.provenance.degraded.length > 0 && (
            <div className="flash caution">
              <AlertIcon size={16} />
              <div>
                <strong>Collection was partial.</strong>
                <p>{act.snapshot.provenance.degraded.join("; ")}. Missing parts are shown as unavailable, not as zero.</p>
              </div>
            </div>
          )}
          <div className="page-grid">
            <LaneBoard scene={act.scene} />
            <aside className="stack" aria-label="Attention and remaining work">
              <Attention items={act.scene.attention} />
              <RemainingWork coordination={act.scene.coordination} issues={act.snapshot.issues} timezone={timezone} />
              <About snapshot={act.snapshot} />
              <Inputs />
            </aside>
          </div>
        </>
      )}
    </>
  );
}

const KIND_LABEL: Record<string, string> = { overlap: "Parallel change", waiting: "Waits on", stale: "Idle" };

function Attention({ items }: { items: SceneAttention[] }) {
  return (
    <section className="box" aria-labelledby="attention-h">
      <div className="box-header">
        <h2 id="attention-h">Needs attention</h2>
        <span className={`counter${items.some((a) => a.kind !== "stale") ? " attention" : ""}`}>{items.length}</span>
      </div>
      {items.length === 0 ? (
        <div className="box-blank">Nothing needs a conversation right now.</div>
      ) : (
        items.map((a) => (
          <div className="box-row" key={`${a.kind}:${a.target}`}>
            <span style={{ color: a.kind === "stale" ? "var(--fg-muted)" : "var(--attention)", marginTop: 2 }}>
              {a.kind === "stale" ? <ClockIcon size={16} /> : <GitPullRequestIcon size={16} />}
            </span>
            <div className="main">
              <div className="title">{a.label}</div>
              <div className="meta">
                {KIND_LABEL[a.kind] ?? a.kind}
                {a.basis && ` · ${a.basis}`}
                {a.confidence && ` · ${a.confidence} confidence`}
              </div>
            </div>
          </div>
        ))
      )}
    </section>
  );
}

function About({ snapshot }: { snapshot: Snapshot }) {
  return (
    <section className="box" aria-labelledby="about-h">
      <div className="box-header">
        <h2 id="about-h">This snapshot</h2>
      </div>
      <div className="box-row">
        <div className="main meta" style={{ display: "grid", gap: 6, marginTop: 0 }}>
          <span>Generated {absolute(snapshot.generated_at)}</span>
          <span>
            Window: last {snapshot.window.hours} h on <code>{snapshot.repository.default_branch ?? "default branch"}</code>
          </span>
          {snapshot.trigger?.event && (
            <span>
              Trigger: <code>{snapshot.trigger.event}</code>
              {snapshot.trigger.sha && (
                <>
                  {" "}
                  at <code>{snapshot.trigger.sha.slice(0, 7)}</code>
                </>
              )}
            </span>
          )}
          <span>
            {snapshot.summary.commits_in_window} commits · {snapshot.summary.areas_active} active areas · {snapshot.summary.open_issues}{" "}
            open issues
          </span>
          {snapshot.repository.url && (
            <a href={snapshot.repository.url} style={{ display: "inline-flex", gap: 6, alignItems: "center" }}>
              <LinkIcon size={16} /> Repository on GitHub
            </a>
          )}
        </div>
      </div>
    </section>
  );
}

function Inputs() {
  const bundle = layout.useLoaderData();
  return (
    <section className="box" aria-labelledby="inputs-h">
      <div className="box-header">
        <h2 id="inputs-h">Inputs</h2>
        <span className="end">
          <Link to="/sources">Details</Link>
        </span>
      </div>
      {(Object.keys(SOURCES) as (keyof typeof SOURCES)[]).map((k) => (
        <div className="box-row" key={k} style={{ padding: "8px 16px" }}>
          <div className="main">
            <div style={{ fontWeight: 500 }}>{SOURCES[k].label}</div>
            <SourceStatus result={bundle[k]} required={SOURCES[k].required} />
          </div>
        </div>
      ))}
    </section>
  );
}
