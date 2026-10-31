import { createFileRoute, getRouteApi } from "@tanstack/react-router";
import { SourceStatus } from "../../components/SourceStatus";
import { absolute } from "../../data/freshness";
import { SOURCES } from "../../data/load";

export const Route = createFileRoute("/_app/sources")({ component: Sources });
const layout = getRouteApi("/_app");

/** Every input, what this view expects from it, and exactly what happened when it loaded. */
function Sources() {
  const bundle = layout.useLoaderData();
  return (
    <section className="box" aria-labelledby="sources-h">
      <div className="box-header">
        <h2 id="sources-h">Data sources</h2>
        <span className="end">loaded {absolute(bundle.receivedAt)}</span>
      </div>
      {(Object.keys(SOURCES) as (keyof typeof SOURCES)[]).map((k) => {
        const spec = SOURCES[k];
        const r = bundle[k];
        return (
          <div className="box-row" key={k}>
            <div className="main">
              <div className="title">
                {spec.label}{" "}
                <span className="label" style={{ marginLeft: 4 }}>
                  {spec.required ? "required" : "optional"}
                </span>
              </div>
              <div className="meta">
                <code>{r.url}</code> · expects <code>{spec.schemaId}</code>
              </div>
              <div style={{ marginTop: 6 }}>
                <SourceStatus result={r} required={spec.required} />
              </div>
              {r.status === "invalid" && (
                <ul className="issues">
                  {r.issues.map((i) => (
                    <li key={i}>
                      <code>{i}</code>
                    </li>
                  ))}
                </ul>
              )}
              {r.status === "unreadable" && (
                <ul className="issues">
                  <li>{r.detail}</li>
                </ul>
              )}
            </div>
          </div>
        );
      })}
    </section>
  );
}
