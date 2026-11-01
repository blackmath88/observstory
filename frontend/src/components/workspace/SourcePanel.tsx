import { useId } from "react";
import type { Bundle } from "../../data/types";
import { publicURL, type RecordView } from "../../view/workspace";

/** Bundle-wide context does not assert that every input supports this record. */
export function SourcePanel({ record, bundle }: { record: RecordView; bundle: Bundle }) {
  const heading = useId();
  const snapshot = bundle.snapshot.status === "ok" ? bundle.snapshot.data : null;
  const knowledge = bundle.knowledge.status === "ok" ? bundle.knowledge.data : null;
  const scene = bundle.scene.status === "ok" ? bundle.scene.data : null;
  const workspace = bundle.workspace.status === "ok" ? bundle.workspace.data : null;
  const rows = [
    { label: "Snapshot", status: bundle.snapshot.status, revision: snapshot?.trigger?.sha, at: snapshot?.generated_at },
    { label: "Scene", status: bundle.scene.status, at: scene?.source.generated_at, revision: undefined },
    { label: "Knowledge", status: bundle.knowledge.status, revision: knowledge?.resolved_commit, at: knowledge?.generated_at },
    { label: "Workspace", status: bundle.workspace.status, revision: workspace?.source_commit, at: undefined },
  ];
  const revisions = rows.map((row) => row.revision).filter((revision): revision is string => !!revision);
  return (
    <section className="source-panel" aria-labelledby={heading}>
      <h3 id={heading}>Sources and provenance</h3>
      {record.material.length ? (
        <ul className="source-material">
          {record.material.map((source) => (
            <li className="source-material-item" key={`${source.title}:${source.url}`}>
              {publicURL(source.url) ? (
                <a href={publicURL(source.url)}>{source.title} ↗</a>
              ) : (
                <span>{source.title} · public link unavailable</span>
              )}
            </li>
          ))}
        </ul>
      ) : (
        <p>No source material linked.</p>
      )}
      {new Set(revisions).size > 1 && (
        <p className="source-caution">Captured input revisions differ. This is not an atomic project state.</p>
      )}
      {knowledge && !knowledge.complete && (
        <p className="source-caution">Knowledge export is partial; selected source material may be absent.</p>
      )}
      {!!snapshot?.provenance.degraded.length && (
        <p className="source-caution">Snapshot collection is partial: {snapshot.provenance.degraded.join("; ")}</p>
      )}
      {rows
        .filter((row) => row.status !== "ok")
        .map((row) => (
          <p key={row.label} className="source-caution">
            {row.label}: {row.status}. Its evidence is unavailable.
          </p>
        ))}
      <details className="source-capture">
        <summary className="source-capture-toggle">Captured input revisions</summary>
        <p>Workspace-wide input context; each record retains its own evidence basis.</p>
        <dl>
          {rows.map((row) => (
            <div className="source-capture-row" key={row.label}>
              <dt>
                {row.label} <span>{row.status === "ok" ? "loaded" : row.status}</span>
              </dt>
              <dd>
                {row.revision && /^(?:[a-f0-9]{40}|[a-f0-9]{64})$/i.test(row.revision) ? (
                  <>
                    <span>Immutable revision</span>
                    <code>{row.revision}</code>
                  </>
                ) : (
                  <span>Immutable revision unavailable</span>
                )}
                <span>{row.at ? `Generated ${row.at}` : "Generation time unavailable"}</span>
              </dd>
            </div>
          ))}
        </dl>
        <p>Loaded captures do not establish current progress or complete history.</p>
      </details>
    </section>
  );
}
