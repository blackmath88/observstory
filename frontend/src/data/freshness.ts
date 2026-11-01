/** Snapshot freshness. The Action runs on push/PR events and an hourly cron, so a snapshot older
 *  than two hours means the observatory has not looked recently. A moving clock in the page
 *  never makes the data fresher; this is always computed from the snapshot's own timestamp. */
export const STALE_AFTER_MS = 2 * 60 * 60 * 1000;

export interface Freshness {
  ageMs: number;
  label: string;
  stale: boolean;
}

export function freshness(generatedAt: string, now: Date): Freshness | null {
  const t = Date.parse(generatedAt);
  if (Number.isNaN(t)) return null;
  const ageMs = Math.max(0, now.getTime() - t);
  return { ageMs, label: ageLabel(ageMs), stale: ageMs > STALE_AFTER_MS };
}

export function ageLabel(ms: number): string {
  const min = Math.floor(ms / 60000);
  if (min < 1) return "just now";
  if (min < 60) return `${min} min ago`;
  const h = Math.floor(min / 60);
  if (h < 48) return `${h} h ago`;
  return `${Math.floor(h / 24)} days ago`;
}

/** Absolute timestamp for titles and tooltips, in the viewer's locale and zone. */
export function absolute(iso: string): string {
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}
