import type { EventSchedule } from "../data/types";

export type ScheduledEvent = EventSchedule["events"][number];

export interface EventClock {
  timezone: string;
  deadline: { label: string; at: string; remainingMs: number; arrived: boolean } | null;
  /** The event happening now, when the programme gives it an end time. */
  current: ScheduledEvent | null;
  /** The next events after now (programme order), excluding the deadline itself. */
  upcoming: ScheduledEvent[];
}

/** Hands-off countdown and the programme around now. Arriving at the deadline marks nothing done:
 *  it only says the time has come (HACKATHON-PROJECT-VIEW.md). */
export function eventClock(schedule: EventSchedule, now: Date): EventClock {
  const t = now.getTime();
  const events = [...schedule.events]
    .filter((e) => !Number.isNaN(Date.parse(e.start_at)))
    .sort((a, b) => Date.parse(a.start_at) - Date.parse(b.start_at));
  const dl = schedule.coding_deadline;
  const deadline =
    dl && !Number.isNaN(Date.parse(dl.at))
      ? { label: dl.label, at: dl.at, remainingMs: Date.parse(dl.at) - t, arrived: Date.parse(dl.at) <= t }
      : null;
  const current = events.find((e) => e.end_at && Date.parse(e.start_at) <= t && t < Date.parse(e.end_at)) ?? null;
  const upcoming = events.filter((e) => Date.parse(e.start_at) > t && e.id !== dl?.event_id).slice(0, 3);
  return { timezone: schedule.timezone, deadline, current, upcoming };
}
