import { BookIcon, CommentDiscussionIcon, LawIcon, LinkExternalIcon } from "@primer/octicons-react";
import { Link } from "@tanstack/react-router";
import type { Knowledge, KnowledgeRecord, SourceResult } from "../../data/types";

const MAX_DECISIONS = 4;
const MAX_QUESTIONS = 5;

/** What are we building, what is decided, what is open. Only what the repository declares. */
export function ProjectNow({ result }: { result: SourceResult<Knowledge> }) {
  if (result.status !== "ok") {
    return (
      <section className="box" aria-labelledby="now-h">
        <div className="box-header">
          <BookIcon size={16} />
          <h2 id="now-h">Project now</h2>
        </div>
        <div className="box-blank">
          {result.status === "missing" ? (
            "This repository does not publish project knowledge yet."
          ) : (
            <>
              Project knowledge could not be read. <Link to="/sources">See Data sources</Link>.
            </>
          )}
        </div>
      </section>
    );
  }
  const k = result.data;
  const sel = k.selection?.current_direction;
  const direction = sel?.record ? k.records.find((r) => r.id === sel.record) : undefined;
  const decisions = k.records.filter((r) => r.type === "decision" && (r.status === "declared" || r.status === "stated"));
  const questions = k.records.filter((r) => r.type === "question" && r.status === "open");
  const declaration = direction?.basis?.declarations?.[0];
  return (
    <section className="box" aria-labelledby="now-h">
      <div className="box-header">
        <BookIcon size={16} />
        <h2 id="now-h">Project now</h2>
        {!k.complete && <span className="label caution">partial</span>}
      </div>
      <div className="box-row">
        <div className="main">
          <div className="eyebrow">Current direction</div>
          {direction ? (
            <>
              <div className="lead">
                <RecordLink record={direction} />
              </div>
              {direction.path && (
                <div className="meta">
                  <code>{direction.path}</code>
                  {" · "}
                  {direction.status}
                </div>
              )}
              {declaration?.quote && (
                <blockquote className="quote">
                  “{clip(declaration.quote, 180)}”
                  <span className="meta">
                    {" "}
                    — declared in {declaration.url ? <a href={declaration.url}>{declaration.path}</a> : declaration.path}
                  </span>
                </blockquote>
              )}
            </>
          ) : (
            <div className="meta">
              No single current direction is declared{sel?.candidates?.length ? ` (${sel.candidates.length} candidates)` : ""}.
            </div>
          )}
        </div>
      </div>
      <div className="box-row">
        <div className="main">
          <div className="eyebrow">
            <LawIcon size={14} /> Decisions <span className="counter">{decisions.length}</span>
          </div>
          {decisions.length === 0 ? (
            <div className="meta">No decisions declared yet.</div>
          ) : (
            <ul className="plain-list">
              {decisions.slice(0, MAX_DECISIONS).map((d) => (
                <li key={d.id}>
                  <span className="label">{d.status}</span> <RecordLink record={d} />
                </li>
              ))}
              {decisions.length > MAX_DECISIONS && <li className="meta">+{decisions.length - MAX_DECISIONS} more</li>}
            </ul>
          )}
        </div>
      </div>
      <div className="box-row">
        <div className="main">
          <div className="eyebrow">
            <CommentDiscussionIcon size={14} /> Open questions <span className="counter">{questions.length}</span>
          </div>
          {questions.length === 0 ? (
            <div className="meta">No open questions declared.</div>
          ) : (
            <ul className="plain-list">
              {questions.slice(0, MAX_QUESTIONS).map((q) => (
                <li key={q.id}>
                  <RecordLink record={q} />
                </li>
              ))}
              {questions.length > MAX_QUESTIONS && <li className="meta">+{questions.length - MAX_QUESTIONS} more</li>}
            </ul>
          )}
        </div>
      </div>
    </section>
  );
}

function RecordLink({ record }: { record: KnowledgeRecord }) {
  const title = record.title.replace(/^.+ › /, "");
  return record.url ? (
    <a href={record.url} title={record.title}>
      {title} <LinkExternalIcon size={12} />
    </a>
  ) : (
    <span title={record.title}>{title}</span>
  );
}

const clip = (s: string, n: number) => (s.length > n ? `${s.slice(0, n - 1)}…` : s);
