"use client";

import { useEffect, useState } from "react";
import type { Fixture } from "@/lib/types";

/**
 * Interpolates the match minute between server updates so the clock feels
 * live even between polls, without ever running ahead of a fresher update.
 */
export function useTickingMinute(fixture: Fixture): number {
  const [display, setDisplay] = useState(fixture.minute);

  useEffect(() => {
    setDisplay(fixture.minute);
    if (fixture.status !== "live") return;
    const baseline = fixture.minute;
    const start = Date.now();
    const id = setInterval(() => {
      const elapsedMinutes = Math.floor((Date.now() - start) / 60000);
      setDisplay(Math.min(baseline + elapsedMinutes, 90));
    }, 1000);
    return () => clearInterval(id);
  }, [fixture.minute, fixture.status]);

  return display;
}
