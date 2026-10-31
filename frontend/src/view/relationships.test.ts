import { describe, expect, it } from "vitest";
import fixture from "../../fixtures/relationships/knowledge.json";
import { loadBundle } from "../data/load";
import { manifestURL, publishedRelationships, relationshipsFor } from "./relationships";
import { type RecordView, workspace } from "./workspace";

async function bundle() {
  return loadBundle(
    "x/",
    async (url) => (url.endsWith("knowledge.json") ? new Response(JSON.stringify(fixture)) : new Response("", { status: 404 })),
    new Date(),
    async () => new Response("", { status: 404 }),
  );
}
const records: RecordView[] = [
  { id: "research", title: "Research", kind: "research", basis: "Declared workspace", material: [] },
  { id: "concept", title: "Concept", kind: "concept", basis: "Declared workspace", material: [] },
];
describe("published relationship evidence", () => {
  it("preserves published direction, raw resolution and quote failures without adding membership or records", async () => {
    const b = await bundle();
    expect(b.knowledge.status).toBe("ok");
    const before = JSON.stringify(b);
    const modelBefore = workspace(b);
    const evidence = publishedRelationships(b, records);
    expect(evidence.knowledgeState).toBe("partial");
    const research = relationshipsFor(evidence, "research");
    expect(research).toHaveLength(2);
    expect(research[0]?.from.id).toBe("research");
    expect(research[0]?.to).toEqual({ id: "concept", title: "Concept", available: true });
    expect(research[0]?.resolved).toBe(false);
    expect(research[0]?.declarations[0]).toMatchObject({ found: false, quote: "Source claim, not an accepted decision.", line: 7 });
    expect(relationshipsFor(evidence, "concept")).toHaveLength(2);
    expect(evidence.links[1]?.to).toEqual({ id: "missing-record", title: "missing-record", available: false });
    expect(evidence.links[1]?.resolved).toBe(true);
    expect(JSON.stringify(b)).toBe(before);
    expect(workspace(b)).toEqual(modelBefore);
    expect(records).toHaveLength(2);
  });
  it("qualifies malformed fields individually and retains separate workspace declarations", async () => {
    const b = await bundle();
    b.workspace = {
      status: "ok",
      url: "x/workspace.json",
      contract: "full",
      data: { schema: "observstory.workspace/v1", records: [], relations: [{ from: "research", to: "concept", type: "supports" }] },
    };
    const e = publishedRelationships(b, records);
    expect(e.unplaced).toBe(2);
    expect(e.links[2]?.unreadable).toBe(true);
    expect(e.links[2]?.declarations[0]).toMatchObject({ path: "Source path unavailable", quote: null, found: null, line: null });
    expect(e.links[2]?.declarations[0]?.url).toBeUndefined();
    expect(relationshipsFor(e, "research").map((link) => link.source)).toEqual([
      "Project knowledge",
      "Project knowledge",
      "Workspace declaration",
    ]);
    expect(e.links.at(-1)?.resolved).toBeNull();
    expect(e.links.at(-1)?.manifestURL).toBeUndefined();
    b.knowledge = { status: "missing", url: "x/knowledge.json" };
    expect(publishedRelationships(b, records)).toMatchObject({ knowledgeState: "missing", workspaceState: "loaded" });
  });
  it("links manifests only to a safe repository, exact commit and relative path", () => {
    const commit = "a".repeat(40);
    expect(manifestURL("owner/repo", commit, ".observstory/knowledge file.json")).toBe(
      `https://github.com/owner/repo/blob/${commit}/.observstory/knowledge%20file.json`,
    );
    for (const path of ["/absolute", "../private", "a/../b", "a//b", "a\u0000b", "."])
      expect(manifestURL("owner/repo", commit, path)).toBeUndefined();
    expect(manifestURL("owner/repo", "main", "a")).toBeUndefined();
    expect(manifestURL("../repo", commit, "a")).toBeUndefined();
    expect(manifestURL("https://github.com/owner/repo", commit, "a")).toBeUndefined();
  });
});
