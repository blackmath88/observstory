import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { loadBundle } from "./load";

/** Opt-in check against real published data kept outside the repository:
 *    OBSERVSTORY_LIVE_DATA=/path/to/downloaded/data npx vitest run
 *  Real consumer data is never committed (fixtures/README.md). */
const dir = process.env.OBSERVSTORY_LIVE_DATA;

describe.skipIf(!dir)("live consumer data", () => {
  it("validates every published source against the frontend's contracts", async () => {
    const fetcher = (url: string) => {
      try {
        return Promise.resolve(new Response(readFileSync(join(dir as string, url.replace(/^live\//, ""))), { status: 200 }));
      } catch {
        return Promise.resolve(new Response("", { status: 404 }));
      }
    };
    const b = await loadBundle("live/", fetcher);
    const summary = Object.fromEntries((["snapshot", "scene", "knowledge", "event"] as const).map((k) => [k, b[k].status]));
    expect(summary).toEqual({ snapshot: "ok", scene: "ok", knowledge: "ok", event: "ok" });
  });
});
