import { useId } from "react";
import { type RelationshipEndpoint, type RelationshipEvidence, relationshipsFor } from "../../view/relationships";

export function RelationshipPanel({
  recordId,
  evidence,
  onOpen,
}: {
  recordId: string;
  evidence: RelationshipEvidence;
  onOpen: (id: string) => void;
}) {
  const heading = useId();
  const links = relationshipsFor(evidence, recordId);
  function endpoint(value: RelationshipEndpoint) {
    if (value.id === recordId) return <span className="relationship-current">{value.title}</span>;
    if (!value.available || value.id === null) return <span className="relationship-missing">{value.title} · unavailable here</span>;
    const id = value.id;
    return (
      <button
        type="button"
        className="text-button relationship-endpoint"
        title={id}
        aria-label={`Open related record: ${value.title}`}
        onClick={() => onOpen(id)}
      >
        {value.title} ↗
      </button>
    );
  }
  return (
    <section className="published-relationships" aria-labelledby={heading}>
      <h3 id={heading}>
        Published relationships <span>{links.length}</span>
      </h3>
      <p className="relationship-inputs">
        Knowledge: {evidence.knowledgeState} · Workspace: {evidence.workspaceState}
      </p>
      {evidence.knowledgeState === "partial" && <p className="relationship-notice">Knowledge is partial; other links may be absent.</p>}
      {evidence.unplaced > 0 && (
        <p className="relationship-notice">
          {evidence.unplaced} published link(s) have no available endpoint and cannot be placed on a record.
        </p>
      )}
      {!links.length && <p>No links for this record in the available relationship inputs.</p>}
      {links.map((edge) => (
        <article key={edge.id} className="published-relationship">
          <div className="relationship-source">
            {edge.source} · {edge.basis.replaceAll("_", " ")}
          </div>
          <div className="relationship-path">
            {endpoint(edge.from)}
            <span className="relationship-verb">{edge.verb.replaceAll("_", " ")} →</span>
            {endpoint(edge.to)}
          </div>
          {edge.source === "Project knowledge" && (
            <p className="relationship-resolution">
              Exporter endpoint check: {edge.resolved === true ? "both present" : edge.resolved === false ? "unresolved" : "unavailable"}
            </p>
          )}
          {edge.unreadable && <p className="relationship-notice">Some published relationship fields are unreadable.</p>}
          <details className="relationship-evidence">
            <summary className="relationship-evidence-toggle">Inspect link evidence</summary>
            {edge.declarations.map((declaration) => (
              <div className="relationship-quote" key={declaration.id}>
                {declaration.quote !== null ? <blockquote>{declaration.quote}</blockquote> : <p>No quoted text supplied.</p>}
                <p>
                  {declaration.url ? (
                    <a href={declaration.url}>
                      {declaration.path}
                      {declaration.line === null ? "" : `:${declaration.line}`} ↗
                    </a>
                  ) : (
                    declaration.path
                  )}
                </p>
                <p>
                  {declaration.found === true
                    ? "Producer found this quote at export."
                    : declaration.found === false
                      ? "Producer did not find this quote at export."
                      : "Quote match was not checked."}
                </p>
              </div>
            ))}
            {!edge.declarations.length && <p>No quoted passage supplied for this manifest link.</p>}
            {edge.manifestURL ? (
              <p>
                <a href={edge.manifestURL}>Inspect manifest at captured commit ↗</a>
              </p>
            ) : (
              <p>No pinned manifest link available.</p>
            )}
          </details>
        </article>
      ))}
    </section>
  );
}
