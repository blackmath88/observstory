import { describe, expect, it } from "vitest";
import { loadBundle } from "../data/load";
import { validate } from "../data/validate";
import { workspace } from "./workspace";

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
