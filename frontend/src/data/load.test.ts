import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { activity, loadBundle, resolveDataBase } from "./load";

const fixtures = join(__dirname, "..", "..", "fixtures");
/** Serves fixture files like a static host: 404 for anything that does not exist. */
const fileFetcher = (url: string) => {
  try {
    return Promise.resolve(new Response(readFileSync(join(fixtures, url)), { status: 200 }));
  } catch {
    return Promise.resolve(new Response("not found", { status: 404 }));
  }
};

describe("loadBundle", () => {
  it("accepts the synthetic hackathon fixture against the repository schemas", async () => {
    const b = await loadBundle("hackathon/data/", fileFetcher);
    expect(b.snapshot.status).toBe("ok");
    expect(b.scene.status).toBe("ok");
    expect(b.event).toMatchObject({ status: "ok", contract: "identity-only" });
    expect(b.knowledge.status).toBe("missing");
    expect(activity(b)).not.toBeNull();
  });

  it("reports an unsupported schema version instead of rendering it", async () => {
    const b = await loadBundle("broken/data/", fileFetcher);
    expect(b.snapshot).toMatchObject({ status: "unsupported", found: "observstory.snapshot/v9", expected: "observstory.snapshot/v1" });
    expect(b.scene.status).toBe("unreadable");
    expect(activity(b)).toBeNull();
  });

  it("reports schema violations with paths", async () => {
    const fetcher = (url: string) =>
      url.endsWith("snapshot.json")
        ? Promise.resolve(new Response(JSON.stringify({ schema: "observstory.snapshot/v1", generated_at: 3 }), { status: 200 }))
        : fileFetcher(`hackathon/data/${url.split("/").pop()}`);
    const b = await loadBundle("x/", fetcher);
    expect(b.snapshot.status).toBe("invalid");
    if (b.snapshot.status === "invalid") expect(b.snapshot.issues.join(" ")).toMatch(/required|generated_at/);
  });

  it("separates an unreachable host from a missing file", async () => {
    const b = await loadBundle("x/", () => Promise.reject(new TypeError("Failed to fetch")));
    expect(b.snapshot).toMatchObject({ status: "unreachable", detail: "Failed to fetch" });
  });
});

describe("resolveDataBase", () => {
  it("defaults to ./data/ next to index.html", () => expect(resolveDataBase("")).toBe("./data/"));
  it("accepts a relative fixture path", () => expect(resolveDataBase("?data=quiet/data")).toBe("quiet/data/"));
  it.each(["https://evil.example/", "//evil.example/data/", "../secret/", "a/../../b/", "javascript:alert(1)"])("refuses %s", (v) =>
    expect(resolveDataBase(`?data=${encodeURIComponent(v)}`)).toBe("./data/"),
  );
});
