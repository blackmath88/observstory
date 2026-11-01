import { ClockIcon, DotFillIcon, GitBranchIcon, GitPullRequestDraftIcon, GitPullRequestIcon } from "@primer/octicons-react";
import { ageLabel } from "../../data/freshness";
import type { Scene, SceneEdge, SceneNode } from "../../data/types";
import { type Lane, lanes } from "../../view/lanes";

/** Lanes with work as GitHub-style lists; lanes with nothing to show collapse into one box. */
export function LaneBoard({ scene }: { scene: Scene }) {
  const l = lanes(scene);
  const byId = new Map(scene.nodes.map((n) => [n.id, n]));
  return (
    <fieldset className="stack lanes-set">
      <legend className="sr-only">Lanes</legend>
      {l.active.length === 0 && (
        <section className="box">
          <div className="box-blank">
            <h3>Nothing in flight</h3>
            No open pull requests or active branches in the last {scene.source.window_hours} h.
          </div>
        </section>
      )}
      {l.active.map((lane) => (
        <LaneBox key={lane.zone.id} lane={lane} edges={l.edgesByNode} byId={byId} />
      ))}
      {l.quiet.length > 0 && (
        <section className="box" aria-labelledby="quiet-h">
          <div className="box-header">
            <h2 id="quiet-h">Quiet lanes</h2>
            <span className="counter">{l.quiet.length}</span>
            <span className="end">no work in flight</span>
          </div>
          {l.quiet.map((q) => (
            <div className="box-row compact" key={q.zone.id}>
              <span className="lane-num mono">{String(q.number).padStart(2, "0")}</span>
              <div className="main">
                <span className="lane-name">{q.zone.label}</span>
                {q.zone.recently_changed.length > 0 && (
                  <span className="meta">
                    {" · recently changed "}
                    {q.zone.recently_changed.map((p, k) => (
                      <span key={p}>
                        {k > 0 && ", "}
                        <code>{p}</code>
                      </span>
                    ))}
                    {q.zone.recently_changed_more > 0 && ` +${q.zone.recently_changed_more}`}
                  </span>
                )}
              </div>
            </div>
          ))}
        </section>
      )}
    </fieldset>
  );
}

function LaneBox({ lane, edges, byId }: { lane: Lane; edges: Map<string, SceneEdge[]>; byId: Map<string, SceneNode> }) {
  const primary = lane.areas.filter((a) => a.nodes.length > 0);
  // Areas changed only by work drawn elsewhere fold into one line, so they never look like work.
  const secondary = lane.areas.filter((a) => a.nodes.length === 0 && a.alsoActive.length > 0);
  return (
    <section className="box" aria-labelledby={`lane-${lane.zone.id}`}>
      <div className="box-header">
        <span className="lane-num mono">{String(lane.number).padStart(2, "0")}</span>
        <h2 id={`lane-${lane.zone.id}`}>{lane.zone.label}</h2>
        {lane.zone.attention && (
          <span className="attention-dot" title="Something in this lane needs a conversation">
            <DotFillIcon size={16} />
          </span>
        )}
        {lane.zone.description && <span className="lane-desc">{lane.zone.description}</span>}
        <span className="end">
          <span className="counter">{lane.zone.in_flight}</span> in flight
        </span>
      </div>
      {primary.map(({ group, nodes }) => (
        <div key={group.id}>
          <div className="area-row">
            <AreaPath path={group.path} />
            {group.age_hours != null && <span className="meta">{ageLabel(group.age_hours * 3.6e6)}</span>}
          </div>
          {nodes.map((n) => (
            <WorkItemRow key={n.id} node={n} edges={edges.get(n.id) ?? []} byId={byId} />
          ))}
        </div>
      ))}
      {secondary.length > 0 && (
        <div className="box-row compact also">
          <span className="meta">
            Also changed here:{" "}
            {secondary.map((a, k) => (
              <span key={a.group.id}>
                {k > 0 && ", "}
                <code>{a.group.path}</code> by {a.alsoActive.map((n) => n.ref).join(", ")}
              </span>
            ))}
          </span>
        </div>
      )}
    </section>
  );
}

/** `apps/commons` → muted parent, bold leaf, like the current Project Map. */
function AreaPath({ path }: { path: string }) {
  const i = path.lastIndexOf("/");
  return (
    <span className="area-path mono">
      {i > 0 && <span className="muted">{path.slice(0, i + 1)}</span>}
      <strong>{i > 0 ? path.slice(i + 1) : path}</strong>
    </span>
  );
}

const REVIEW: Record<string, string> = {
  no_reviewer: "no reviewer",
  review_requested: "review requested",
  approved: "approved",
  changes_requested: "changes requested",
  commented: "commented",
};

export function WorkItemRow({ node, edges, byId }: { node: SceneNode; edges: SceneEdge[]; byId: Map<string, SceneNode> }) {
  const Icon =
    node.status === "stale"
      ? ClockIcon
      : node.kind === "branch"
        ? GitBranchIcon
        : node.status === "draft"
          ? GitPullRequestDraftIcon
          : GitPullRequestIcon;
  const isBranch = node.kind === "branch";
  const authors = [...node.actors].sort((a, b) => a.localeCompare(b));
  return (
    <div className={`box-row item${node.status === "stale" || node.status === "landed" ? " faded" : ""}`}>
      <span className="item-icon" title={statusWord(node)}>
        <Icon size={16} />
      </span>
      <div className="main">
        <div className="item-title">
          {isBranch && <span className="label">branch</span>}{" "}
          {node.url ? (
            <a href={node.url} className={isBranch ? "mono-title" : undefined}>
              {node.label}
            </a>
          ) : (
            <span>{node.label}</span>
          )}
          {!isBranch && <span className="muted"> {node.ref}</span>}
          {edges.map((e) => {
            const other = byId.get(e.from === node.id ? e.to : e.from);
            const ref = other?.ref ?? (e.from === node.id ? e.to : e.from);
            const text =
              e.type === "overlap" ? `parallel change · ${ref}` : e.from === node.id ? `waits on ${ref}` : `${ref} waits on this`;
            return (
              <span key={e.id} className={`label${e.type === "overlap" ? " attention" : ""}`} style={{ marginLeft: 6 }}>
                {text}
              </span>
            );
          })}
        </div>
        <div className="meta">
          {[
            authors.length ? authors.join(", ") : null,
            node.age_hours != null ? ageLabel(node.age_hours * 3.6e6) : null,
            node.review_state ? (REVIEW[node.review_state] ?? node.review_state.replace(/_/g, " ")) : null,
            node.status !== "in_flight" ? statusWord(node) : null,
            node.also_touches.length ? `+${node.also_touches.length} area${node.also_touches.length > 1 ? "s" : ""}` : null,
          ]
            .filter(Boolean)
            .join(" · ")}
          {node.flags.map((f) => (
            <span key={f} className="label subtle" style={{ marginLeft: 6 }}>
              {f.replace(/_/g, " ")}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

const statusWord = (n: SceneNode) => ({ in_flight: "in flight", draft: "draft", stale: "stale", landed: "landed" })[n.status] ?? n.status;
