import { AlertIcon, ClockIcon, DotFillIcon, GitPullRequestIcon, LinkIcon } from "@primer/octicons-react";
import { createFileRoute, getRouteApi, Link } from "@tanstack/react-router";
import { SourceStatus } from "../../components/SourceStatus";
import { absolute } from "../../data/freshness";
import { activity, SOURCES } from "../../data/load";
import type { Scene, SceneAttention, Snapshot } from "../../data/types";

export const Route = createFileRoute("/_app/")({ component: Overview });
const layout = getRouteApi("/_app");

function Overview() {
  const bundle = layout.useLoaderData();
  const act = activity(bundle);
  if (!act) {
    return (
      <div className="flash danger" role="alert">
        <AlertIcon size={16} />
        <div>
          <strong>Activity is unavailable.</strong>
          <p>
            The snapshot and scene are both needed to show work in flight. Nothing is shown as zero.{" "}
            <Link to="/sources">See what went wrong in Data sources</Link>.
          </p>
        </div>
      </div>
    );
  }
  const { snapshot, scene } = act;
  return (
    <>
      <Stats snapshot={snapshot} />
      {snapshot.provenance.degraded.length > 0 && (
        <div className="flash caution">
          <AlertIcon size={16} />
          <div>
            <strong>Collection was partial.</strong>
            <p>{snapshot.provenance.degraded.join("; ")}. Missing parts are shown as unavailable, not as zero.</p>
          </div>
        </div>
      )}
      <div className="page-grid">
        <div style={{ display: "grid", gap: 24, minWidth: 0 }}>
          <Attention items={scene.attention} />
          <Lanes scene={scene} />
        </div>
        <aside style={{ display: "grid", gap: 24, minWidth: 0 }} aria-label="About this snapshot">
          <About snapshot={snapshot} />
          <Inputs />
        </aside>
      </div>
    </>
  );
}

function Stats({ snapshot }: { snapshot: Snapshot }) {
  const s = snapshot.summary;
  const items: [number, string, boolean][] = [
    [s.in_flight, "in flight", false],
    [s.signals.overlap, s.signals.overlap === 1 ? "overlap" : "overlaps", s.signals.overlap > 0],
    [s.signals.waiting, "waiting", s.signals.waiting > 0],
    [s.signals.stale, "stale", false],
  ];
  return (
    <section className="box stats" aria-label="Project summary">
      {items.map(([n, label, attn]) => (
        <div className="stat" key={label}>
          <div className={`n${attn ? " attention" : ""}`}>{n}</div>
          <div className="l">{label}</div>
        </div>
      ))}
    </section>
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

/** A compact first pass of the lanes; the full board arrives in the next slice. Quiet lanes
 *  take one line instead of a full column. */
function Lanes({ scene }: { scene: Scene }) {
  const zones = [...scene.zones].sort((a, b) => a.order - b.order);
  return (
    <section className="box" aria-labelledby="lanes-h">
      <div className="box-header">
        <h2 id="lanes-h">Lanes</h2>
        <span className="end">
          {zones.filter((z) => z.state === "active").length} active · {zones.length} total
        </span>
      </div>
      {zones.map((z, i) => (
        <div className="box-row" key={z.id}>
          <span className="mono muted" style={{ marginTop: 1 }}>
            {String(i + 1).padStart(2, "0")}
          </span>
          <div className="main">
            <div className="title">
              {z.label}
              {z.attention && (
                <span style={{ color: "var(--attention)", marginLeft: 6 }} title="Something here needs a conversation">
                  <DotFillIcon size={16} />
                </span>
              )}
            </div>
            <div className="meta">
              {z.state === "quiet" ? "quiet" : `${z.in_flight} in flight`}
              {z.recently_changed.length > 0 && (
                <>
                  {" · recently changed "}
                  {z.recently_changed.map((p, k) => (
                    <span key={p}>
                      {k > 0 && ", "}
                      <code>{p}</code>
                    </span>
                  ))}
                  {z.recently_changed_more > 0 && ` +${z.recently_changed_more}`}
                </>
              )}
            </div>
          </div>
        </div>
      ))}
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
