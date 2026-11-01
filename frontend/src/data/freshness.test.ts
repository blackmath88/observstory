import { describe, expect, it } from "vitest";
import { ageLabel, freshness } from "./freshness";

describe("freshness", () => {
  const now = new Date("2026-10-31T14:00:00Z");
  it("labels recent snapshots in minutes and keeps them fresh", () =>
    expect(freshness("2026-10-31T13:50:00Z", now)).toMatchObject({ label: "10 min ago", stale: false }));
  it("marks snapshots older than two hours as stale", () =>
    expect(freshness("2026-10-31T11:00:00Z", now)).toMatchObject({ label: "3 h ago", stale: true }));
  it("returns null for an unparseable timestamp instead of inventing an age", () => expect(freshness("soon", now)).toBeNull());
  it("never reports a negative age for clock skew", () => expect(ageLabel(-5000)).toBe("just now"));
});
