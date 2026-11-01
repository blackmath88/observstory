import { describe, expect, it } from "vitest";
import { boardColumns, readBoardGrouping } from "./board";
import type { RecordView } from "./workspace";

const records: RecordView[] = [
  { id: "root", title: "Root", kind: "workstream", basis: "Declared workspace", material: [] },
  {
    id: "paper",
    title: "Study",
    kind: "research",
    basis: "Selected knowledge · document complete",
    material: [{ title: "Source", url: "https://example.com/paper" }],
  },
  { id: "concept", title: "Idea", kind: "concept", basis: "Selected knowledge · document proposed", material: [] },
  { id: "plan", title: "Plan", kind: "plan", basis: "Declared workspace", material: [] },
  { id: "artifact", title: "Change", kind: "implementation", basis: "Observed pull_request · landed (artifact state)", material: [] },
  { id: "paused", title: "Exploration", kind: "support", status: "paused", basis: "Declared workspace", material: [] },
  { id: "question", title: "Question", kind: "question", basis: "Selected knowledge · document open", material: [] },
];

describe("board browsing projection", () => {
  it("partitions all records exactly once by kind while preserving source order and evidence", () => {
    const before = JSON.stringify(records);
    const columns = boardColumns(records, "kind");
    expect(columns.map((c) => c.label)).toEqual(["Research", "Concepts", "Planning", "Implementation", "Other context"]);
    expect(
      columns
        .flatMap((c) => c.records)
        .map((r) => r.id)
        .sort(),
    ).toEqual(records.map((r) => r.id).sort());
    expect(columns.find((c) => c.id === "context")?.records.map((r) => r.id)).toEqual(["root", "paused", "question"]);
    expect(columns[0]?.records[0]?.material).toEqual(records[1]?.material);
    expect(JSON.stringify(records)).toBe(before);
  });
  it("does not convert document completion, proposed concepts or landed artifacts into lifecycle", () => {
    const columns = boardColumns(records, "lifecycle");
    expect(columns.map((c) => c.label)).toEqual(["Undeclared", "paused"]);
    expect(columns[0]?.records.map((r) => r.id)).toEqual(["root", "paper", "concept", "plan", "artifact", "question"]);
    expect(columns[1]?.records.map((r) => r.id)).toEqual(["paused"]);
    const declared: RecordView = {
      id: "declared",
      title: "Declared proposal",
      kind: "concept",
      status: "proposed",
      basis: "Declared workspace",
      material: [],
    };
    expect(boardColumns([...records, declared], "lifecycle").map((c) => c.label)).toEqual(["Undeclared", "paused", "proposed"]);
  });
  it("does not manufacture empty phases and defaults unsupported navigation to kind", () => {
    expect(boardColumns([], "kind")).toEqual([]);
    expect(boardColumns([], "lifecycle")).toEqual([]);
    expect(readBoardGrouping("lifecycle")).toBe("lifecycle");
    expect(readBoardGrouping("future")).toBe("kind");
  });
});
