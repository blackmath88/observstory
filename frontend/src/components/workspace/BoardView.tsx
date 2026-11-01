import { useId, useLayoutEffect, useRef } from "react";
import { type BoardGrouping, boardColumns } from "../../view/board";
import type { RecordView } from "../../view/workspace";

export function BoardView({
  records,
  grouping,
  selection,
  onGroup,
  onOpen,
}: {
  records: RecordView[];
  grouping: BoardGrouping;
  selection: string | null;
  onGroup: (grouping: BoardGrouping) => void;
  onOpen: (id: string) => void;
}) {
  const columns = boardColumns(records, grouping);
  const scrollport = useRef<HTMLDivElement>(null);
  const resultIds = JSON.stringify(records.map((record) => record.id));
  const previousResults = useRef({ grouping, resultIds });
  useLayoutEffect(() => {
    if (previousResults.current.grouping === grouping && previousResults.current.resultIds === resultIds) return;
    previousResults.current = { grouping, resultIds };
    // A new grouping/result set starts at its first card. Selection and clock updates
    // retain scroll so a drawer returns to the same place.
    scrollport.current?.scrollTo({ top: 0, left: 0, behavior: "instant" });
  }, [grouping, resultIds]);
  const prefix = useId();
  const headings = useRef(new Map<string, HTMLHeadingElement>());
  const navigation = useRef<HTMLElement>(null);
  function jump(id: string) {
    const heading = headings.current.get(id);
    heading?.focus({ preventScroll: true });
    heading?.scrollIntoView({ block: "nearest", inline: "start", behavior: "instant" });
  }
  function backToColumns() {
    navigation.current?.scrollIntoView({ block: "nearest", behavior: "instant" });
    navigation.current?.querySelector<HTMLButtonElement>("button")?.focus({ preventScroll: true });
  }
  return (
    <>
      <div className="board-tools">
        <div className="board-tools-heading">
          <h2>Board</h2>
          <span className="board-summary">
            {records.length} records · {records.filter((record) => record.status === undefined).length} lifecycle undeclared
          </span>
        </div>
        <fieldset className="board-grouping" aria-label="Board grouping">
          <button type="button" className="board-group-button" aria-pressed={grouping === "kind"} onClick={() => onGroup("kind")}>
            By kind
          </button>
          <button type="button" className="board-group-button" aria-pressed={grouping === "lifecycle"} onClick={() => onGroup("lifecycle")}>
            By lifecycle
          </button>
        </fieldset>
        <p>
          {grouping === "kind"
            ? "Browse record kinds. Lifecycle stays separate on each card."
            : "Only declared lifecycle is grouped here. Document and artifact states remain evidence."}
        </p>
        {columns.length > 0 && (
          <nav ref={navigation} className="board-column-nav" aria-label="Board columns">
            {columns.map((column) => (
              <button
                type="button"
                key={column.id}
                className="board-jump"
                onClick={() => jump(column.id)}
                aria-label={`Jump to ${column.label} column (${column.records.length} records)`}
              >
                {column.label} <span className="board-jump-count">{column.records.length}</span>
              </button>
            ))}
          </nav>
        )}
      </div>
      <div ref={scrollport} className={`workspace-board ${columns.length === 1 ? "single" : ""}`}>
        {columns.map((column, index) => (
          <section className="board-column" data-group-id={column.id} key={column.id} aria-labelledby={`${prefix}-${index}`}>
            <h2
              id={`${prefix}-${index}`}
              tabIndex={-1}
              ref={(node) => {
                if (node) headings.current.set(column.id, node);
                else headings.current.delete(column.id);
              }}
            >
              {column.label} <span className="board-jump-count">{column.records.length}</span>
            </h2>
            <div className="board-cards">
              {column.records.map((record) => (
                <button
                  type="button"
                  data-record-id={record.id}
                  className={`board-card ${selection === record.id ? "selected" : ""}`}
                  key={record.id}
                  onClick={() => onOpen(record.id)}
                >
                  <div className="board-card-meta">
                    <small>{record.kind}</small>
                    <span className="board-lifecycle">
                      {record.status === undefined ? "Lifecycle undeclared" : `Declared: ${record.status}`}
                    </span>
                  </div>
                  <strong>{record.title}</strong>
                  {record.context && <span className="board-context">{record.context}</span>}
                  <span className="board-evidence">{record.basis}</span>
                </button>
              ))}
            </div>
            <button type="button" className="board-return text-button" onClick={backToColumns}>
              Back to board columns ↑
            </button>
          </section>
        ))}
      </div>
    </>
  );
}
