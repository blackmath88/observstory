import { useEffect, useRef, useState } from "react";
import type { Bundle } from "../../data/types";
import { useNow } from "../../lib/useNow";
import { type BoardGrouping, readBoardGrouping } from "../../view/board";
import { publishedRelationships, type RelationshipEvidence } from "../../view/relationships";
import {
  instantPosition,
  periodPosition,
  readTimelineRange,
  recordTiming,
  type TimelineAxis,
  type TimelineRange,
  timelineAxis,
  timelineTime,
} from "../../view/timeline";
import {
  FOCUSES,
  type Focus,
  publicURL,
  type RecordView,
  readFocus,
  scopeWorkspace,
  workspace,
  workspaceLocations,
} from "../../view/workspace";
import { EventClock } from "../overview/EventClock";
import { BoardView } from "./BoardView";
import { RelationshipPanel } from "./RelationshipPanel";

function preference<T>(key: string, fallback: T): T {
  try {
    return JSON.parse(localStorage.getItem(key) ?? "null") ?? fallback;
  } catch {
    return fallback;
  }
}

export function WorkspaceView({ bundle }: { bundle: Bundle }) {
  const model = workspace(bundle);
  const relationshipEvidence = publishedRelationships(bundle, model.records);
  const key = `observatory:${bundle.base}:`;
  const [expanded, setExpanded] = useState<string[]>(() => preference(`${key}expanded`, []));
  const [board, setBoard] = useState(() => new URLSearchParams(window.location.hash.split("?")[1]).get("view") === "board");
  const [selection, setSelection] = useState(() => new URLSearchParams(window.location.hash.split("?")[1]).get("item"));
  const [focus, setFocus] = useState(() => readFocus(new URLSearchParams(window.location.hash.split("?")[1]).get("focus")));
  const [query, setQuery] = useState(() => new URLSearchParams(window.location.hash.split("?")[1]).get("q") ?? "");
  const [revealId, setRevealId] = useState(() => new URLSearchParams(window.location.hash.split("?")[1]).get("reveal"));
  const [range, setRange] = useState(() => readTimelineRange(new URLSearchParams(window.location.hash.split("?")[1]).get("range")));
  const [grouping, setGrouping] = useState(() => readBoardGrouping(new URLSearchParams(window.location.hash.split("?")[1]).get("group")));
  const now = useNow();
  const scope = scopeWorkspace(model, focus, query, revealId);
  const trigger = useRef<HTMLElement | null>(null);
  const lastSelection = useRef(selection);
  const lastReveal = useRef<string | null>(null);
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
      setFocus(readFocus(p.get("focus")));
      setQuery(p.get("q") ?? "");
      setRevealId(p.get("reveal"));
      setRange(readTimelineRange(p.get("range")));
      setGrouping(readBoardGrouping(p.get("group")));
    };
    window.addEventListener("hashchange", sync);
    window.addEventListener("popstate", sync);
    return () => {
      window.removeEventListener("hashchange", sync);
      window.removeEventListener("popstate", sync);
    };
  }, []);
  useEffect(() => {
    if (selection) {
      lastSelection.current = selection;
      return;
    }
    const locating = revealId !== lastReveal.current;
    lastReveal.current = revealId;
    const frame = requestAnimationFrame(() => {
      const fallback = [...document.querySelectorAll<HTMLElement>("button[data-record-id]")].find(
        (element) => element.dataset.recordId === (revealId ?? lastSelection.current),
      );
      const target = locating && revealId ? fallback : trigger.current?.isConnected ? trigger.current : fallback;
      if (revealId && (locating || !trigger.current?.isConnected)) target?.scrollIntoView({ block: "center", behavior: "instant" });
      target?.focus({ preventScroll: true });
    });
    return () => cancelAnimationFrame(frame);
  }, [selection, revealId]);
  function navigate(
    item: string | null,
    view = board,
    push = true,
    nextFocus: Focus = focus,
    nextQuery = query,
    nextReveal = revealId,
    nextRange: TimelineRange = range,
    nextGrouping: BoardGrouping = grouping,
  ) {
    if (view) nextReveal = null;
    const p = new URLSearchParams();
    if (view) p.set("view", "board");
    if (item) p.set("item", item);
    if (nextFocus !== "all") p.set("focus", nextFocus);
    if (nextQuery) p.set("q", nextQuery);
    if (nextReveal) p.set("reveal", nextReveal);
    if (nextRange !== "recent") p.set("range", nextRange);
    if (nextGrouping !== "kind") p.set("group", nextGrouping);
    const hash = `#/${p.size ? `?${p}` : ""}`;
    const drawerReturn = !!item && ((!selection && push) || (!!selection && !!window.history.state?.drawerReturn));
    window.history[push ? "pushState" : "replaceState"]({ workspace: true, drawerReturn }, "", hash);
    setSelection(item);
    setBoard(view);
    setFocus(nextFocus);
    setQuery(nextQuery);
    setRevealId(nextReveal);
    setRange(nextRange);
    setGrouping(nextGrouping);
  }
  function open(id: string) {
    if (!document.activeElement?.closest("dialog")) trigger.current = document.activeElement as HTMLElement;
    navigate(id, board, !selection);
  }
  function close() {
    if (window.history.state?.drawerReturn) window.history.back();
    else navigate(null, board, false);
  }
  function endReveal() {
    trigger.current = document.querySelector<HTMLInputElement>(".workspace-search input");
    navigate(null, board, true, focus, query, null);
  }
  function toggle(id: string) {
    setExpanded((prev) => (prev.includes(id) ? prev.filter((v) => v !== id) : [...prev, id]));
  }
  function renderRecord(r: RecordView, path: string[] = []): React.ReactNode {
    if (path.includes(r.id) || !scope.visible.has(r.id)) return null;
    const children = (r.members ?? []).map((id) => model.byId.get(id)).filter((v): v is RecordView => !!v);
    const isExpanded = scope.active || scope.revealAncestors.has(r.id) || expanded.includes(r.id);
    return (
      <div key={r.id} className={scope.active && !scope.matching.has(r.id) && r.id !== revealId ? "scope-ancestor" : undefined}>
        <RecordRow
          record={r}
          depth={path.length}
          selected={selection === r.id || (!selection && revealId === r.id)}
          expanded={isExpanded}
          onToggle={scope.active || scope.revealAncestors.has(r.id) ? undefined : () => toggle(r.id)}
          onOpen={open}
          axis={axis}
        />
        {isExpanded && (
          <div className="workstream-children">
            {children.map((child) => renderRecord(child, [...path, r.id]))}
            {!scope.active &&
              model.relations
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
            {!scope.active && !children.length && <p className="row-context">{r.context ?? r.basis}. No additional membership declared.</p>}
          </div>
        )}
      </div>
    );
  }
  const axis = timelineAxis(
    model.records.filter((record) => scope.visible.has(record.id)),
    range,
    now.getTime(),
  );
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
        <span role="status">
          {scope.matches.length} of {model.records.length} records · read only
        </span>
      </div>
      <div className="workspace-filters">
        <fieldset className="focus-switch" aria-label="Record category">
          {FOCUSES.map((f) => (
            <button type="button" key={f.id} aria-pressed={focus === f.id} onClick={() => navigate(selection, board, true, f.id)}>
              {f.label} <span className="focus-count">{scopeWorkspace(model, f.id, query).matches.length}</span>
            </button>
          ))}
        </fieldset>
        <label className="workspace-search">
          <span>Find records</span>
          <input
            type="search"
            value={query}
            placeholder="Title, context, source…"
            onChange={(e) => navigate(selection, board, false, focus, e.target.value)}
          />
        </label>
      </div>
      {scope.active && (
        <p className="scope-note">
          Filtered by record kind and text. Overview keeps containing workstreams visible for context.{" "}
          <button type="button" className="text-button" onClick={() => navigate(selection, board, true, "all", "")}>
            Clear filters
          </button>
        </p>
      )}
      {scope.revealed && (
        <div className="reveal-notice" role="status">
          <div>
            <strong className="reveal-title">Located in Overview: {scope.revealed.title}</strong>
            <span className="reveal-description">
              {scope.matching.has(scope.revealed.id)
                ? "Your filters and saved expansion are unchanged."
                : "Outside your current filters. Temporarily shown with its containing records; your filters are unchanged."}
            </span>
          </div>
          <button type="button" className="text-button end-reveal" onClick={endReveal}>
            End reveal
          </button>
        </div>
      )}
      {revealId && !scope.revealed && (
        <p className="workspace-notice" role="status">
          Revealed record is unavailable in this input.{" "}
          <button type="button" className="text-button" onClick={() => navigate(selection, board, false, focus, query, null)}>
            End reveal
          </button>
        </p>
      )}
      <div className="workspace-layout">
        <section className="workstreams" aria-label={board ? "Board" : "Workstreams"}>
          {scope.matches.length === 0 && !scope.revealed && model.records.length > 0 && (
            <div className="box-blank">
              <h2>No matching records</h2>
              <p>Try another category or search term. Missing results do not imply no work.</p>
              <button type="button" className="text-button" onClick={() => navigate(selection, board, true, "all", "")}>
                Clear filters
              </button>
            </div>
          )}
          {board ? (
            <BoardView
              records={scope.matches}
              grouping={grouping}
              selection={selection}
              onOpen={open}
              onGroup={(next) => navigate(selection, board, true, focus, query, revealId, range, next)}
            />
          ) : (
            <>
              <div className="workspace-heading">
                <h2>Workstreams</h2>
                <span>Stable order · expand for context</span>
              </div>
              <div className="timeline-controls">
                <fieldset aria-label="Timeline range">
                  <button
                    type="button"
                    aria-pressed={range === "recent"}
                    onClick={() => navigate(selection, board, true, focus, query, revealId, "recent")}
                  >
                    Recent window
                  </button>
                  <button
                    type="button"
                    aria-pressed={range === "fit"}
                    onClick={() => navigate(selection, board, true, focus, query, revealId, "fit")}
                  >
                    Fit evidence
                  </button>
                </fieldset>
                <p>
                  {range === "recent" ? "Last 6 hours · next 2 hours" : "Fits results and containing records, including collapsed members"}
                </p>
              </div>
              <div className="timeline-summary" role="status">
                <span>
                  {timelineTime(axis.min)} — {timelineTime(axis.max)} UTC
                </span>
                <span>
                  {axis.dated} dated · {axis.undated} undated{axis.outside ? ` · ${axis.outside} with dates outside this window` : ""}
                </span>
                <span>Points: latest recorded activity. Bands: calendar target precision, never work duration.</span>
                {axis.empty && <span>No dated records. Window is based on the clock.</span>}
                {axis.clockOutside && <span>Now is {axis.clockOutside} this window.</span>}
              </div>
              <div className="workstream-axis">
                <span className="timeline-axis-title">Work & context · UTC</span>
                <div className="timeline-ticks">
                  {axis.ticks.map((tick) => (
                    <span
                      key={tick.value}
                      className="timeline-tick"
                      style={{
                        left: `${tick.position}%`,
                        transform: `translateX(-${tick.position === 0 ? 0 : tick.position === 100 ? 100 : 50}%)`,
                      }}
                      title={new Date(tick.value).toISOString()}
                    >
                      {tick.label}
                    </span>
                  ))}
                </div>
              </div>
              {model.roots.map((r) => renderRecord(r))}
              {!model.records.length && <p className="box-blank">No workspace records available. Inspect Data sources.</p>}
              <div className="workspace-legend">
                <span className="legend-now" /> Now <span className="legend-planned" /> Planned target <span className="legend-event" />{" "}
                Observed activity · never duration · planned bands show calendar precision
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
        <Detail
          key={selected.id}
          record={selected}
          records={model.byId}
          relationshipEvidence={relationshipEvidence}
          onOpen={open}
          onClose={close}
          onReveal={() => {
            trigger.current = null;
            navigate(null, false, true, focus, query, selected.id);
          }}
        />
      )}
    </>
  );
}

function RecordRow({
  record: r,
  depth = 0,
  selected,
  expanded,
  onToggle,
  onOpen,
  axis,
}: {
  record: RecordView;
  depth?: number;
  selected: boolean;
  expanded?: boolean;
  onToggle?: () => void;
  onOpen: (id: string) => void;
  axis: TimelineAxis;
}) {
  const timing = recordTiming(r);
  const observed = instantPosition(timing.observed, axis);
  const planned = periodPosition(timing.planned, axis);
  const clock = instantPosition(axis.now, axis);
  return (
    <div className={`workstream-row ${selected ? "selected" : ""}`}>
      <div className="row-identity" style={{ paddingLeft: `${16 + Math.min(depth, 5) * 14}px` }}>
        {onToggle ? (
          <button type="button" className="expand-row" aria-label={`Expand ${r.title}`} aria-expanded={expanded} onClick={onToggle}>
            {expanded ? "⌄" : "›"}
          </button>
        ) : (
          <span className="branch-joint">↳</span>
        )}
        <button
          type="button"
          className="record-button"
          aria-current={selected ? "location" : undefined}
          data-record-id={r.id}
          onClick={() => onOpen(r.id)}
        >
          <strong>{r.title}</strong>
          <span>
            {r.kind} <b>·</b> {r.status ?? "Lifecycle undeclared"}
          </span>
          <small>{r.context ?? r.basis}</small>
        </button>
      </div>
      <div className="row-time">
        <div className="time-track">
          {clock.position !== null && <i className="workspace-now" aria-hidden="true" style={{ left: `${clock.position}%` }} />}
          {planned && !planned.outside && (
            <button
              type="button"
              className={`planned-bar ${planned.clipped ? "clipped" : ""}`}
              style={{ left: `${planned.left}%`, width: `${planned.width}%` }}
              aria-label={`Inspect planned target for ${r.title}`}
              onClick={() => onOpen(r.id)}
            />
          )}
          {observed.position !== null && (
            <button
              type="button"
              className="observed-point"
              style={{ left: `${observed.position}%` }}
              aria-label={`Inspect observed activity for ${r.title}`}
              title={r.observed}
              onClick={() => onOpen(r.id)}
            />
          )}
        </div>
        <div className="time-captions">
          {r.planned && (
            <button type="button" className="time-caption" onClick={() => onOpen(r.id)}>
              {r.milestone ? "◇ Milestone target" : "Planned target"}: {r.planned.start}
              {r.planned.end ? ` → ${r.planned.end}` : ""} · {r.planned.precision} precision
              {planned?.outside
                ? ` · ${planned.outside === "before" ? "Before" : "After"} window`
                : planned?.clipped
                  ? " · Extends beyond window"
                  : !planned
                    ? " · Date unavailable"
                    : ""}
            </button>
          )}
          {r.observed && (
            <button type="button" className="time-caption" onClick={() => onOpen(r.id)} title={r.observed}>
              Observed {timing.observed === null ? "date unavailable" : `${timelineTime(timing.observed)} UTC`}
              {observed.outside ? ` · ${observed.outside === "before" ? "Before" : "After"} window` : ""}
            </button>
          )}
          {!r.planned && !r.observed && <span className="no-date">No date</span>}
        </div>
      </div>
    </div>
  );
}

function Detail({
  record: r,
  records,
  relationshipEvidence,
  onOpen,
  onClose,
  onReveal,
}: {
  record: RecordView;
  records: Map<string, RecordView>;
  relationshipEvidence: RelationshipEvidence;
  onOpen: (id: string) => void;
  onClose: () => void;
  onReveal: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const locations = workspaceLocations([...records.values()], r.id);
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
        <section className="detail-locations" aria-labelledby="locations-title">
          <h3 id="locations-title">Location in workspace</h3>
          {locations.paths.length === 1 && locations.paths[0]?.length === 1 ? (
            <p>Top-level record. No containing record is published.</p>
          ) : (
            <nav aria-label="Workspace locations">
              {locations.paths.map((path) => (
                <ol key={JSON.stringify(path.map((part) => part.id))}>
                  {path.map((part) => (
                    <li key={part.id}>
                      {part.id === r.id ? (
                        <span aria-current="location">{part.title}</span>
                      ) : (
                        <button type="button" className="text-button" onClick={() => onOpen(part.id)}>
                          {part.title}
                        </button>
                      )}
                      <small>{part.basis}</small>
                    </li>
                  ))}
                </ol>
              ))}
            </nav>
          )}
          {locations.truncated && <p>Additional workspace locations are omitted from this preview.</p>}
          {locations.cyclic && <p>A membership cycle prevents resolving some workspace locations.</p>}
          <button type="button" className="reveal-button" onClick={onReveal} disabled={!locations.paths.length}>
            Reveal in Overview ↗
          </button>
        </section>
        <section>
          <h3>Context</h3>
          <p>{r.context ?? "No additional purpose is declared."}</p>
          <p className="meta">{r.basis}</p>
        </section>
        <RelationshipPanel recordId={r.id} evidence={relationshipEvidence} onOpen={onOpen} />
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
