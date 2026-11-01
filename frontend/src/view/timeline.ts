import type { RecordView } from "./workspace";

const HOUR = 3_600_000;
export type TimelineRange = "recent" | "fit";
export function readTimelineRange(value: string | null): TimelineRange {
  return value === "fit" ? "fit" : "recent";
}
export interface Period {
  start: number;
  end: number;
}

/** Calendar targets have no time of day. UTC boundaries keep their printed date stable;
 * the end is exclusive and describes target precision, never observed work duration. */
export function plannedPeriod(planned: RecordView["planned"]): Period | null {
  if (!planned) return null;
  const pattern = { day: /^\d{4}-\d{2}-\d{2}$/, month: /^\d{4}-\d{2}$/, year: /^\d{4}$/ }[planned.precision];
  const values = [planned.start, planned.end ?? planned.start];
  if (values.some((value) => !pattern.test(value) || !Number.isFinite(Date.parse(value)))) return null;
  const start = Date.parse(planned.start);
  const endDate = new Date(Date.parse(planned.end ?? planned.start));
  if (values.some((value) => new Date(Date.parse(value)).toISOString().slice(0, value.length) !== value)) return null;
  if (planned.precision === "day") endDate.setUTCDate(endDate.getUTCDate() + 1);
  if (planned.precision === "month") endDate.setUTCMonth(endDate.getUTCMonth() + 1);
  if (planned.precision === "year") endDate.setUTCFullYear(endDate.getUTCFullYear() + 1);
  const end = endDate.getTime();
  return end > start ? { start, end } : null;
}
export function recordTiming(record: RecordView) {
  const parsed = record.observed ? Date.parse(record.observed) : Number.NaN;
  return { planned: plannedPeriod(record.planned), observed: Number.isFinite(parsed) ? parsed : null };
}

export function timelineAxis(records: RecordView[], mode: TimelineRange, now: number) {
  const timings = records.map(recordTiming);
  const dates = timings.flatMap((t) => [
    ...(t.planned ? [t.planned.start, t.planned.end] : []),
    ...(t.observed === null ? [] : [t.observed]),
  ]);
  let min = now - 6 * HOUR;
  let max = now + 2 * HOUR;
  if (mode === "fit" && dates.length) {
    const first = Math.min(...dates);
    const last = Math.max(...dates);
    const center = first + (last - first) / 2;
    const span = Math.max(HOUR, last - first) * 1.2;
    min = center - span / 2;
    max = center + span / 2;
  }
  const bounds = { min, max };
  const undated = timings.filter((t) => !t.planned && t.observed === null).length;
  const outside = timings.filter(
    (t) => (t.observed !== null && (t.observed < min || t.observed > max)) || (t.planned && (t.planned.start < min || t.planned.end > max)),
  ).length;
  const ticks = Array.from({ length: 5 }, (_, index) => {
    const value = min + ((max - min) * index) / 4;
    const label = new Intl.DateTimeFormat("en-GB", {
      timeZone: "UTC",
      ...(max - min > 48 * HOUR
        ? { day: "numeric", month: "short", year: "numeric" }
        : { hour: "2-digit", minute: "2-digit", hourCycle: "h23" }),
    }).format(value);
    return { value, label, position: index * 25 };
  });
  return {
    ...bounds,
    now,
    mode,
    ticks,
    undated,
    dated: records.length - undated,
    outside,
    empty: !dates.length,
    clockOutside: now < min ? "before" : now > max ? "after" : null,
  };
}
export type TimelineAxis = ReturnType<typeof timelineAxis>;

export function instantPosition(value: number | null, axis: Pick<TimelineAxis, "min" | "max">) {
  if (value === null) return { position: null, outside: null };
  if (value < axis.min) return { position: null, outside: "before" as const };
  if (value > axis.max) return { position: null, outside: "after" as const };
  return { position: ((value - axis.min) / (axis.max - axis.min)) * 100, outside: null };
}
export function periodPosition(period: Period | null, axis: Pick<TimelineAxis, "min" | "max">) {
  if (!period) return null;
  if (period.end <= axis.min) return { outside: "before" as const, left: 0, width: 0, clipped: false };
  if (period.start >= axis.max) return { outside: "after" as const, left: 0, width: 0, clipped: false };
  const start = Math.max(period.start, axis.min);
  const end = Math.min(period.end, axis.max);
  return {
    outside: null,
    left: ((start - axis.min) / (axis.max - axis.min)) * 100,
    width: ((end - start) / (axis.max - axis.min)) * 100,
    clipped: start !== period.start || end !== period.end,
  };
}
export function timelineTime(value: number) {
  return new Intl.DateTimeFormat("en-GB", {
    timeZone: "UTC",
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  }).format(value);
}
