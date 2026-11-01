import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import type { EventSchedule, Scene } from "../data/types";
import { eventClock } from "./clock";
import { lanes } from "./lanes";
import { mission } from "./mission";
import { duration, zoned } from "./time";

const fixture = (f: string) => JSON.parse(readFileSync(join(__dirname, "..", "..", "fixtures", f), "utf8"));
const schedule: EventSchedule = {
  schema: "observstory.event-schedule/v0",
  title: "t",
  timezone: "Europe/Zurich",
  coding_deadline: { event_id: "sun-hands-off", at: "2026-11-01T12:00:00+01:00", label: "Hands off!" },
  events: [
    { id: "sun-breakfast", label: "Breakfast", start_at: "2026-11-01T08:00:00+01:00", end_at: "2026-11-01T09:00:00+01:00" },
    { id: "sun-hands-off", label: "Hands off!", start_at: "2026-11-01T12:00:00+01:00" },
    { id: "sun-presentations", label: "Presentations", start_at: "2026-11-01T13:00:00+01:00" },
  ],
};

describe("event clock (HACKATHON-PROJECT-VIEW acceptance)", () => {
  it("at 11:30 Sunday Zurich shows 30 minutes to hands-off and the 13:00 block separately", () => {
    const c = eventClock(schedule, new Date("2026-11-01T11:30:00+01:00"));
    expect(c.deadline).toMatchObject({ arrived: false });
    expect(duration(c.deadline?.remainingMs ?? 0)).toBe("30 min");
    expect(c.upcoming.map((e) => e.id)).toEqual(["sun-presentations"]);
  });
  it("at noon says hands-off has arrived, without claiming anything is done", () => {
    const c = eventClock(schedule, new Date("2026-11-01T12:00:00+01:00"));
    expect(c.deadline?.arrived).toBe(true);
  });
  it("knows the event happening now when the programme gives an end", () =>
    expect(eventClock(schedule, new Date("2026-11-01T08:30:00+01:00")).current?.id).toBe("sun-breakfast"));
  it("prints times in the event's timezone", () => expect(zoned("2026-11-01T11:00:00Z", "Europe/Zurich")).toBe("Sun 12:00"));
});

describe("mission", () => {
  it("reports no confirmed checkpoints rather than all gates passed", () => {
    const m = mission(
      { sessions: [{ id: "S1", label: "Kickoff", at: "2026-10-31T10:00:00+01:00" }], gates: [], proposed_pending: 12 },
      new Date(),
    );
    expect(m).toMatchObject({ confirmedCheckpoints: 0, proposedPending: 12, next: null });
  });
  it("a gate whose time has passed is still not passed unless reconciled so", () => {
    const m = mission(
      { gates: [{ id: "G1", label: "Freeze", at: "2026-10-01T10:00:00Z", passed: false }] },
      new Date("2026-10-02T00:00:00Z"),
    );
    expect(m?.items[0]).toMatchObject({ kind: "gate", state: "upcoming" });
    expect(m?.nowIndex).toBe(1);
  });
  it("returns null when nothing is declared", () => expect(mission(null, new Date())).toBeNull());
});

describe("lanes", () => {
  it("collapses lanes with nothing to show and draws each work item once", () => {
    const scene = fixture("hackathon/data/scene.json") as Scene;
    const l = lanes(scene);
    const drawn = l.active.flatMap((x) => x.areas.flatMap((a) => a.nodes.map((n) => n.id)));
    expect(new Set(drawn).size).toBe(drawn.length);
    expect(drawn.length).toBe(scene.nodes.length);
    expect(l.quiet.every((q) => q.areas.every((a) => a.nodes.length === 0))).toBe(true);
  });
});
