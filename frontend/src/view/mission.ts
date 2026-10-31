import type { Coordination } from "../data/types";

export type MissionItem =
  | { kind: "session"; id: string; at: string; label: string; sub: string; openQuestions: string[] }
  | { kind: "gate"; id: string; at: string; label: string; sub: string; state: "passed" | "next" | "upcoming"; confirmedBy?: string };

export interface Mission {
  items: MissionItem[];
  /** Index in `items` where "now" falls (items before it are in the past). */
  nowIndex: number;
  confirmedCheckpoints: number;
  proposedPending: number;
  next: { label: string; at: string; hours: number | null } | null;
}

/** Declared sessions and gates in time order. "No gates" is reported as no confirmed checkpoints,
 *  never as "all gates passed"; a gate's time passing does not make it passed. */
export function mission(c: Coordination | null | undefined, now: Date): Mission | null {
  if (!c) return null;
  const sessions: MissionItem[] = (c.sessions ?? []).map((s) => ({
    kind: "session",
    id: s.id,
    at: s.at,
    label: s.label,
    sub: s.kind ?? "session",
    openQuestions: s.open_questions ?? [],
  }));
  const gates: MissionItem[] = (c.gates ?? []).map((g) => ({
    kind: "gate",
    id: g.id,
    at: g.at,
    label: g.label,
    sub: g.kind ?? "gate",
    state: g.passed ? "passed" : g.next ? "next" : "upcoming",
    confirmedBy: g.confirmed_by,
  }));
  const items = [...sessions, ...gates].sort((a, b) => Date.parse(a.at) - Date.parse(b.at));
  const nowIndex = items.filter((i) => Date.parse(i.at) <= now.getTime()).length;
  const nextGate = (c.gates ?? []).find((g) => g.id === c.next_gate) ?? (c.gates ?? []).find((g) => g.next);
  return {
    items,
    nowIndex,
    confirmedCheckpoints: gates.length,
    proposedPending: c.proposed_pending ?? 0,
    next: nextGate ? { label: nextGate.label, at: nextGate.at, hours: c.hours_to_next ?? null } : null,
  };
}
