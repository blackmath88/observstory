import { useEffect, useState } from "react";

/** The current time, refreshed on an interval. Only labels move; data freshness is always
 *  computed from the snapshot's own timestamp. */
export function useNow(intervalMs = 60_000): Date {
  const [now, setNow] = useState(() => new Date());
  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), intervalMs);
    return () => clearInterval(id);
  }, [intervalMs]);
  return now;
}
