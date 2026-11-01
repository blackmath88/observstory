import { FOCUSES, type RecordView, recordFocus } from "./workspace";

export type BoardGrouping = "kind" | "lifecycle";
export function readBoardGrouping(value: string | null): BoardGrouping {
  return value === "lifecycle" ? "lifecycle" : "kind";
}
export interface BoardColumn {
  id: string;
  label: string;
  records: RecordView[];
}

/** Grouping is a browsing projection, never a lifecycle classifier. Keep source order
 * inside columns; evidence strings and document/artifact states cannot create lifecycle. */
export function boardColumns(records: RecordView[], grouping: BoardGrouping): BoardColumn[] {
  if (grouping === "kind") {
    return FOCUSES.filter((focus) => focus.id !== "all")
      .map((focus) => ({
        id: focus.id,
        label: focus.label,
        records: records.filter((record) => recordFocus(record) === focus.id),
      }))
      .filter((column) => column.records.length > 0);
  }
  const columns = new Map<string, BoardColumn>();
  for (const record of records) {
    const id = record.status === undefined ? "missing" : `declared:${record.status}`;
    const column = columns.get(id) ?? { id, label: record.status ?? "Undeclared", records: [] };
    column.records.push(record);
    columns.set(id, column);
  }
  return [...columns.values()];
}
