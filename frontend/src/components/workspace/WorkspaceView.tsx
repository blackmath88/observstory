import { useEffect, useRef, useState } from "react";
import type { Bundle } from "../../data/types";
import { publicURL, type RecordView, workspace } from "../../view/workspace";
import { EventClock } from "../overview/EventClock";

function preference<T>(key: string, fallback: T): T {
  try {
    return JSON.parse(localStorage.getItem(key) ?? "null") ?? fallback;
  } catch {
    return fallback;
  }
}

export function WorkspaceView({ bundle }: { bundle: Bundle }) {
  const model = workspace(bundle);
  const key = `observatory:${bundle.base}:`;
  const [expanded, setExpanded] = useState<string[]>(() => preference(`${key}expanded`, []));
  const [board, setBoard] = useState(() => new URLSearchParams(window.location.hash.split("?")[1]).get("view") === "board");
  const [selection, setSelection] = useState(() => new URLSearchParams(window.location.hash.split("?")[1]).get("item"));
  const trigger = useRef<HTMLElement | null>(null);
  const selected = model.byId.get(selection ?? "");
  useEffect(() => {
    try {
      localStorage.setItem(`${key}expanded`, JSON.stringify(expanded));
    } catch {
      /* private browser */
    }
  }, [expanded, key]);
  useEffect(() => {
    const sync = () => {
      const p = new URLSearchParams(window.location.hash.split("?")[1]);
      setSelection(p.get("item"));
      setBoard(p.get("view") === "board");
    };
    window.addEventListener("hashchange", sync);
    window.addEventListener("popstate", sync);
    return () => {
      window.removeEventListener("hashchange", sync);
      window.removeEventListener("popstate", sync);
    };
  }, []);
  useEffect(() => {
    if (!selection)
      requestAnimationFrame(() => {
        if (trigger.current?.isConnected) trigger.current.focus({ preventScroll: true });
      });
  }, [selection]);
  function navigate(item: string | null, view = board, push = true) {
    const p = new URLSearchParams();
    if (view) p.set("view", "board");
    if (item) p.set("item", item);
    const hash = `#/${p.size ? `?${p}` : ""}`;
    window.history[push ? "pushState" : "replaceState"]({ workspace: true }, "", hash);
    setSelection(item);
    setBoard(view);
  }
  function open(id: string) {
    if (!document.activeElement?.closest("dialog")) trigger.current = document.activeElement as HTMLElement;
    navigate(id, board, !selection);
  }
  function close() {
    if (window.history.state?.workspace) window.history.back();
    else navigate(null, board, false);
  }
  function toggle(id: string) {
    setExpanded((prev) => (prev.includes(id) ? prev.filter((v) => v !== id) : [...prev, id]));
  }
  const dated = model.records
    .flatMap((r) => [r.observed, r.planned?.start, r.planned?.end])
    .filter((v): v is string => !!v && Number.isFinite(Date.parse(v)));
  const now = Date.now();
  const min = Math.min(now - 86400000, ...dated.map(Date.parse));
  const max = Math.max(now + 86400000, ...dated.map(Date.parse));
  const axis = { min, max, now };
  return (
    <>
      <section className="workspace-mission" aria-labelledby="mission-h">
        <div>
          <div className="eyebrow">PROJECT WORKSPACE</div>
          <h1 id="mission-h">{model.direction?.title ?? "Project direction is undeclared"}</h1>
          <p>
            {model.direction?.basis?.declarations?.[0]?.quote ??
              "Selected context, declared workstreams and observed implementation, together."}
          </p>
        </div>
        <div className="mission-source">
          <span>Source revisions</span>
          {[...new Set(model.revisions)].map((r) => (
            <code key={r}>{r.slice(0, 7)}</code>
          ))}
          <span>Static evidence · no inferred progress</span>
        </div>
      </section>
      {model.warnings.map((w) => (
        <p className="workspace-notice" role="status" key={w}>
          {w}
        </p>
      ))}
      <div className="workspace-toolbar">
        <fieldset className="view-switch" aria-label="Workspace view">
          <button type="button" aria-pressed={!board} onClick={() => navigate(selection, false)}>
            Overview
          </button>
          <button type="button" aria-pressed={board} onClick={() => navigate(selection, true)}>
            Board
          </button>
        </fieldset>
        <span>{model.records.length} records · read only</span>
      </div>
      <div className="workspace-layout">
        <section className="workstreams" aria-label={board ? "Board" : "Workstreams"}>
          {board ? (
            <div className="workspace-board">
              {[...new Set(model.records.map((r) => r.status ?? "Undeclared"))].map((status) => (
                <section className="board-column" key={status}>
                  <h2>
                    {status} <span>{model.records.filter((r) => (r.status ?? "Undeclared") === status).length}</span>
                  </h2>
                  {model.records
                    .filter((r) => (r.status ?? "Undeclared") === status)
                    .map((r) => (
                      <button
                        type="button"
                        className={`board-card ${selection === r.id ? "selected" : ""}`}
                        key={r.id}
                        onClick={() => open(r.id)}
                      >
                        <small>{r.kind}</small>
                        <strong>{r.title}</strong>
                        <span>{r.basis}</span>
                      </button>
                    ))}
                </section>
              ))}
            </div>
          ) : (
            <>
              <div className="workspace-heading">
                <h2>Workstreams</h2>
                <span>Stable order · expand for context</span>
              </div>
              <div className="workstream-axis">
                <span>Work & context</span>
                <div>
                  <span>{new Date(min).toLocaleDateString()}</span>
                  <span>Planned: outline · observed: point</span>
                  <span>{new Date(max).toLocaleDateString()}</span>
                </div>
              </div>
              {model.roots.map((r) => (
                <div key={r.id}>
                  <RecordRow
                    record={r}
                    selected={selection === r.id}
                    expanded={expanded.includes(r.id)}
                    onToggle={() => toggle(r.id)}
                    onOpen={open}
                    axis={axis}
                  />
                  {expanded.includes(r.id) && (
                    <div className="workstream-children">
                      {(r.members ?? [])
                        .map((id) => model.byId.get(id))
                        .filter((v): v is RecordView => !!v)
                        .map((child) => (
                          <RecordRow key={child.id} record={child} selected={selection === child.id} onOpen={open} axis={axis} />
                        ))}
                      {model.relations
                        .filter((e) => e.to === r.id || e.from === r.id)
                        .map((e) => (
                          <button
                            type="button"
                            className="relation-link"
                            key={`${e.from}:${e.type}:${e.to}`}
                            onClick={() => open(e.from === r.id ? e.to : e.from)}
                          >
                            {model.byId.get(e.from)?.title} <span>{e.type.replaceAll("_", " ")}</span> {model.byId.get(e.to)?.title} ↗
                          </button>
                        ))}
                      {!r.members?.length && <p className="row-context">{r.context ?? r.basis}. No additional membership declared.</p>}
                    </div>
                  )}
                </div>
              ))}
              {!model.records.length && <p className="box-blank">No workspace records available. Inspect Data sources.</p>}
              <div className="workspace-legend">
                <span className="legend-now" /> Now <span className="legend-planned" /> Planned target <span className="legend-event" />{" "}
                Observed activity · never duration
              </div>
            </>
          )}
        </section>
        <aside className="workspace-support" aria-label="Judgment and resumption">
          <section>
            <h2>
              <span className="attention-symbol">◉</span> Needs you
            </h2>
            {model.records
              .filter((r) => r.attention)
              .map((r) => (
                <button type="button" className="support-link" key={r.id} onClick={() => open(r.id)}>
                  <strong>{r.title}</strong>
                  <span>{r.attention}</span>
                </button>
              ))}
            {!model.records.some((r) => r.attention) && (
              <p>No explicit human judgment request is published. Open questions remain in the workstreams.</p>
            )}
          </section>
          <section>
            <h2>↳ Resume</h2>
            {model.records
              .filter((r) => r.resume)
              .map((r) => (
                <button type="button" className="support-link" key={r.id} onClick={() => open(r.id)}>
                  <strong>{r.title}</strong>
                  <span>{r.resume?.next_action}</span>
                </button>
              ))}
            {!model.records.some((r) => r.resume) && <p>No stopping point or next action has been declared.</p>}
          </section>
          <details className="schedule-disclosure">
            <summary>Event schedule</summary>
            <EventClock result={bundle.event} />
          </details>
        </aside>
      </div>
      {selection && !selected && (
        <p role="alert">
          Selected record is unavailable in this input.{" "}
          <button type="button" onClick={close}>
            Back to workspace
          </button>
        </p>
      )}
      {selected && (
        <Detail key={selected.id} record={selected} records={model.byId} relations={model.relations} onOpen={open} onClose={close} />
      )}
    </>
  );
}

function RecordRow({
  record: r,
  selected,
  expanded,
  onToggle,
  onOpen,
  axis,
}: {
  record: RecordView;
  selected: boolean;
  expanded?: boolean;
  onToggle?: () => void;
  onOpen: (id: string) => void;
  axis: { min: number; max: number; now: number };
}) {
  const position = (date: string | number) =>
    Math.max(0, Math.min(100, (((typeof date === "number" ? date : Date.parse(date)) - axis.min) / (axis.max - axis.min)) * 100));
  return (
    <div className={`workstream-row ${selected ? "selected" : ""}`}>
      <div className="row-identity">
        {onToggle ? (
          <button type="button" className="expand-row" aria-label={`Expand ${r.title}`} aria-expanded={expanded} onClick={onToggle}>
            {expanded ? "⌄" : "›"}
          </button>
        ) : (
          <span className="branch-joint">↳</span>
        )}
        <button type="button" className="record-button" onClick={() => onOpen(r.id)}>
          <strong>{r.title}</strong>
          <span>
            {r.kind} <b>·</b> {r.status ?? "Lifecycle undeclared"}
          </span>
          <small>{r.context ?? r.basis}</small>
        </button>
      </div>
      <div className="row-time">
        <div className="time-track">
          <i className="workspace-now" style={{ left: `${position(axis.now)}%` }} />
          {r.planned ? (
            <>
              <span
                className={r.milestone ? "planned-milestone" : "planned-bar"}
                style={{
                  left: `${position(r.planned.start)}%`,
                  width: `${Math.max(1, position(r.planned.end ?? r.planned.start) - position(r.planned.start))}%`,
                }}
              />
              <span className="time-caption">
                {r.milestone ? "Milestone target" : "Planned"} {r.planned.start}
                {r.planned.end ? ` → ${r.planned.end}` : ""} · {r.planned.precision} precision
              </span>
            </>
          ) : (
            !r.observed && <span className="no-date">No date</span>
          )}
          {r.observed && (
            <>
              <span className="observed-point" style={{ left: `${position(r.observed)}%` }} />
              <span className="time-caption">Observed {r.observed}</span>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function Detail({
  record: r,
  records,
  relations,
  onOpen,
  onClose,
}: {
  record: RecordView;
  records: Map<string, RecordView>;
  relations: { from: string; to: string; type: string }[];
  onOpen: (id: string) => void;
  onClose: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const d = dialog.current;
    d?.showModal();
    return () => d?.close();
  }, []);
  return (
    <dialog
      ref={dialog}
      className="workspace-detail"
      aria-labelledby="detail-title"
      onCancel={(e) => {
        e.preventDefault();
        onClose();
      }}
    >
      <header>
        <span>RECORD DETAIL</span>
        <button type="button" onClick={onClose}>
          ← Back to workspace
        </button>
      </header>
      <div className="detail-body">
        <p className="eyebrow">
          {r.kind} · {r.status ?? "Lifecycle undeclared"}
        </p>
        <h2 id="detail-title">{r.title}</h2>
        <section>
          <h3>Context</h3>
          <p>{r.context ?? "No additional purpose is declared."}</p>
          <p className="meta">{r.basis}</p>
          {relations
            .filter((e) => e.from === r.id || e.to === r.id)
            .map((e) => (
              <button
                type="button"
                className="relation-link"
                key={`${e.from}:${e.type}:${e.to}`}
                onClick={() => onOpen(e.from === r.id ? e.to : e.from)}
              >
                {records.get(e.from)?.title} · {e.type.replaceAll("_", " ")} · {records.get(e.to)?.title} ↗
              </button>
            ))}
        </section>
        <section>
          <h3>Material</h3>
          {r.material.length ? (
            r.material.map((s) => (
              <p key={`${s.title}:${s.url}`}>
                <a href={publicURL(s.url)}>{s.title} ↗</a>
              </p>
            ))
          ) : (
            <p>No source material linked.</p>
          )}
          {(r.members ?? []).map((id) => (
            <p key={id}>
              <button type="button" className="text-button" onClick={() => onOpen(id)}>
                {records.get(id)?.title ?? `${id} (unavailable)`} ↗
              </button>
            </p>
          ))}
        </section>
        <section>
          <h3>Resume</h3>
          {r.resume ? (
            <>
              <p>
                <strong>Stopping point</strong>
                <br />
                {r.resume.stopping_point}
              </p>
              <p>
                <strong>Next action</strong>
                <br />
                {r.resume.next_action}
              </p>
            </>
          ) : (
            <p>No stopping point or next action declared.</p>
          )}
        </section>
        <section>
          <h3>History</h3>
          {r.planned && (
            <p>
              Planned target: {r.planned.start}
              {r.planned.end ? ` → ${r.planned.end}` : ""} ({r.planned.precision} precision). Not an observed duration.
            </p>
          )}
          <p>{r.observed ? `Observed artifact activity: ${r.observed}` : "No observed event is attached to this record."}</p>
          <p className="meta">
            Loaded source data is not a complete historical ledger. A merged artifact does not establish deployment or human acceptance.
          </p>
        </section>
      </div>
    </dialog>
  );
}
