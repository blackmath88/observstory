import { describe, expect, it } from "vitest";
import { loadBundle } from "../data/load";
import { validate } from "../data/validate";
import { type RecordView, readFocus, scopeWorkspace, workspace, workspaceLocations } from "./workspace";

describe("workspace evidence semantics", () => {
  it("keeps missing inputs honest and does not manufacture progress", async () => {
    const b = await loadBundle(
      "x/",
      async () => new Response("", { status: 404 }),
      new Date(),
      async () => new Response("", { status: 404 }),
    );
    const m = workspace(b);
    expect(m.records).toEqual([]);
    expect(m.warnings.join(" ")).toContain("Activity is unavailable");
    expect(m.warnings.join(" ")).toContain("Workspace missing");
  });
  it("preserves declaration order, undated research and explicit paused resume context", async () => {
    const declaration = {
      schema: "observstory.workspace/v1",
      records: [
        { id: "root", title: "Work", kind: "workstream", members: ["research"] },
        {
          id: "research",
          title: "Research",
          kind: "research",
          status: "paused",
          resume: { stopping_point: "Question open", next_action: "Inspect source" },
        },
      ],
      relations: [{ from: "research", to: "root", type: "supports" }],
    };
    const b = await loadBundle(
      "x/",
      async (url) => (url.endsWith("workspace.json") ? new Response(JSON.stringify(declaration)) : new Response("", { status: 404 })),
      new Date(),
      async () => new Response("", { status: 404 }),
    );
    const m = workspace(b);
    expect(m.records.map((r) => r.id)).toEqual(["root", "research"]);
    expect(m.roots.map((r) => r.id)).toEqual(["root"]);
    expect(m.byId.get("research")?.planned).toBeUndefined();
    expect(m.byId.get("research")?.resume?.next_action).toBe("Inspect source");
    expect(m.relations[0]?.type).toBe("supports");
  });
  it("rejects unsupported declaration fields and unsafe public links", () => {
    expect(
      validate("workspace", {
        schema: "observstory.workspace/v1",
        records: [{ id: "x", title: "X", kind: "plan", owner: "invented" }],
        relations: [],
      }).ok,
    ).toBe(false);
    expect(
      validate("workspace", {
        schema: "observstory.workspace/v1",
        records: [{ id: "x", title: "X", kind: "plan", sources: ["javascript:alert(1)"] }],
        relations: [],
      }).ok,
    ).toBe(false);
  });
  it("rejects duplicate IDs, cyclic membership and reversed planned targets", () => {
    const record = { id: "a", title: "A", kind: "plan" };
    expect(validate("workspace", { schema: "observstory.workspace/v1", records: [record, record], relations: [] }).ok).toBe(false);
    expect(validate("workspace", { schema: "observstory.workspace/v1", records: [{ ...record, members: ["a"] }], relations: [] }).ok).toBe(
      false,
    );
    expect(
      validate("workspace", {
        schema: "observstory.workspace/v1",
        records: [{ ...record, planned: { start: "2026-11-01", end: "2026-10-31", precision: "day" } }],
        relations: [],
      }).ok,
    ).toBe(false);
  });
});

describe("shared workspace navigation", () => {
  const records: RecordView[] = [
    { id: "parent", title: "Declared workstream", kind: "workstream", members: ["area"], basis: "Declared", material: [] },
    { id: "area", title: "Nested area", kind: "implementation", members: ["paper", "artifact"], basis: "Derived", material: [] },
    {
      id: "paper",
      title: "Retrieval study",
      kind: "research",
      basis: "Selected knowledge · document current",
      material: [{ title: "CLAIMS.md" }],
    },
    {
      id: "artifact",
      title: "Implement retrieval",
      kind: "implementation",
      basis: "Observed pull_request · landed (artifact state)",
      material: [],
    },
    { id: "question", title: "Open question", kind: "question", basis: "Selected knowledge", material: [] },
  ];
  const model = {
    records,
    byId: new Map(records.map((r) => [r.id, r])),
    roots: records.filter((r) => r.id === "parent" || r.id === "question"),
    relations: [],
    warnings: [],
    revisions: [],
    direction: undefined,
  };
  it("shows matching records and their entire ancestor chain without inventing membership or lifecycle", () => {
    const before = JSON.stringify(model.records);
    const scope = scopeWorkspace(model, "research", "  RETRIEVAL claims  ");
    expect(scope.matches.map((r) => r.id)).toEqual(["paper"]);
    expect([...scope.visible].sort()).toEqual(["area", "paper", "parent"]);
    expect(scope.matching.has("parent")).toBe(false);
    expect(JSON.stringify(model.records)).toBe(before);
    expect(scope.matches[0]?.status).toBeUndefined();
  });
  it("reveals a record outside filters without adding it to results or exposing unrelated descendants", () => {
    const before = JSON.stringify(model.records);
    const scoped = scopeWorkspace(model, "plan", "no match", "artifact");
    expect(scoped.matches).toEqual([]);
    expect([...scoped.visible].sort()).toEqual(["area", "artifact", "parent"]);
    expect(scoped.revealed?.id).toBe("artifact");
    expect(scopeWorkspace(model, "plan", "no match").visible.size).toBe(0);
    expect(scopeWorkspace(model, "plan", "no match", "missing").revealed).toBeUndefined();
    expect(JSON.stringify(model.records)).toBe(before);
  });
  it("retains all membership routes and their evidence basis, without using conceptual relations", () => {
    const other: RecordView = {
      id: "other",
      title: "Other declared container",
      kind: "workstream",
      members: ["paper"],
      basis: "Declared",
      material: [],
    };
    const locations = workspaceLocations([...records, other], "paper");
    expect(locations.paths.map((path) => path.map((r) => r.id))).toEqual([
      ["parent", "area", "paper"],
      ["other", "paper"],
    ]);
    expect(locations.paths[0]?.map((r) => r.basis)).toEqual(["Declared", "Derived", "Selected knowledge · document current"]);
    expect(workspaceLocations(records, "question").paths.map((path) => path.map((r) => r.id))).toEqual([["question"]]);
    expect(workspaceLocations(records, "unavailable").paths).toEqual([]);
  });
  it("bounds location traversal and reports cyclic or omitted routes", () => {
    const parents = Array.from(
      { length: 13 },
      (_, i): RecordView => ({ id: `p${i}`, title: "Container", kind: "workstream", members: ["paper"], basis: "Declared", material: [] }),
    );
    const many = workspaceLocations([...records.filter((r) => r.id === "paper"), ...parents], "paper");
    expect(many.paths).toHaveLength(12);
    expect(many.truncated).toBe(true);
    const cyclic = records.map((r) => (r.id === "area" ? { ...r, members: ["paper", "parent"] } : r));
    expect(workspaceLocations(cyclic, "paper").cyclic).toBe(true);
    expect(workspaceLocations(cyclic, "paper").paths).toEqual([]);
  });
  it("keeps unknown kinds as other context and combines kind and text filters", () => {
    expect(scopeWorkspace(model, "context", "question").matches.map((r) => r.id)).toEqual(["question"]);
    expect(scopeWorkspace(model, "implementation", "retrieval").matches.map((r) => r.id)).toEqual(["artifact"]);
    expect(scopeWorkspace(model, "research", "landed").matches).toEqual([]);
    expect(scopeWorkspace(model, "all", " ").matches).toEqual(records);
    expect(readFocus("invented")).toBe("all");
  });
});
