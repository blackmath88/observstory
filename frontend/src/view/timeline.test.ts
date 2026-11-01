import { describe, expect, it } from "vitest";
import { instantPosition, periodPosition, plannedPeriod, readTimelineRange, recordTiming, timelineAxis, timelineTime } from "./timeline";
import type { RecordView } from "./workspace";

const now = Date.parse("2026-10-31T19:30:00Z");
const record = (fields: Partial<RecordView>): RecordView => ({
  id: "r",
  title: "Record",
  kind: "research",
  basis: "Declared",
  material: [],
  ...fields,
});

describe("timeline evidence semantics", () => {
  it("preserves calendar precision without inventing milestone times or durations", () => {
    expect(plannedPeriod({ start: "2026-11-01", precision: "day" })).toEqual({
      start: Date.parse("2026-11-01T00:00:00Z"),
      end: Date.parse("2026-11-02T00:00:00Z"),
    });
    const month = plannedPeriod({ start: "2028-02", precision: "month" });
    expect(month).toEqual({ start: Date.parse("2028-02-01T00:00:00Z"), end: Date.parse("2028-03-01T00:00:00Z") });
    expect(plannedPeriod({ start: "2026", end: "2027", precision: "year" })).toEqual({
      start: Date.parse("2026-01-01T00:00:00Z"),
      end: Date.parse("2028-01-01T00:00:00Z"),
    });
    expect(plannedPeriod({ start: "2026-02-31", precision: "day" })).toBeNull();
    expect(plannedPeriod({ start: "2026-11", end: "2026-10", precision: "month" })).toBeNull();
    expect(plannedPeriod({ start: "2026-10-31", precision: "month" })).toBeNull();
  });
  it("does not clamp out-of-range observations into fake boundary events", () => {
    const records = [
      record({ observed: "2026-10-01T12:00:00Z" }),
      record({ id: "later", observed: "2026-11-01T12:00:00Z" }),
      record({ id: "unknown" }),
    ];
    const axis = timelineAxis(records, "recent", now);
    expect(axis.min).toBe(now - 6 * 3_600_000);
    expect(axis.max).toBe(now + 2 * 3_600_000);
    expect(axis.outside).toBe(2);
    expect(axis.undated).toBe(1);
    expect(instantPosition(recordTiming(records[0] as RecordView).observed, axis)).toEqual({ position: null, outside: "before" });
    expect(instantPosition(Date.parse("2026-11-01T12:00:00Z"), axis)).toEqual({ position: null, outside: "after" });
    expect(instantPosition(null, axis)).toEqual({ position: null, outside: null });
  });
  it("fits actual evidence independently of the moving clock and leaves records unchanged", () => {
    const records = [record({ observed: "2020-01-01T12:00:00Z" }), record({ id: "unknown" })];
    const before = JSON.stringify(records);
    const axis = timelineAxis(records, "fit", now);
    expect(axis.max - axis.min).toBeGreaterThanOrEqual(3_600_000);
    expect(axis.max).toBeLessThan(now);
    expect(axis.clockOutside).toBe("after");
    expect(axis.outside).toBe(0);
    expect(axis.undated).toBe(1);
    expect(JSON.stringify(records)).toBe(before);
  });
  it("clips planned periods explicitly and keeps both evidence channels independent", () => {
    const r = record({
      planned: { start: "2026-10-31", end: "2026-11-01", precision: "day" },
      observed: "2026-10-31T18:38:00Z",
      milestone: true,
    });
    const timing = recordTiming(r);
    const axis = timelineAxis([r], "recent", now);
    expect(periodPosition(timing.planned, axis)).toEqual({ left: 0, width: 100, outside: null, clipped: true });
    expect(instantPosition(timing.observed, axis).position).not.toBeNull();
    expect(axis.outside).toBe(1);
    const future = plannedPeriod({ start: "2027", precision: "year" });
    expect(periodPosition(future, axis)).toEqual({ left: 0, width: 0, outside: "after", clipped: false });
  });
  it("keeps undated or unavailable evidence explicit and formats all axis labels in UTC", () => {
    const axis = timelineAxis([record({})], "fit", now);
    expect(axis.empty).toBe(true);
    expect(axis.dated).toBe(0);
    expect(axis.undated).toBe(1);
    expect(axis.ticks.map((tick) => tick.label)).toEqual(["13:30", "15:30", "17:30", "19:30", "21:30"]);
    expect(timelineTime(now)).toContain("19:30");
    expect(recordTiming(record({ observed: "unavailable" })).observed).toBeNull();
    expect(readTimelineRange("invented")).toBe("recent");
  });
});
