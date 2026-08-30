"use client";

import { useTickingMinute } from "@/hooks/useTickingMinute";
import { formatClock } from "@/lib/time";
import type { Fixture } from "@/lib/types";

export default function MatchHeader({ fixture }: { fixture: Fixture }) {
  const minute = useTickingMinute(fixture);
  const clock = formatClock(fixture.status, minute);
  const isLive = fixture.status === "live";

  return (
    <div className="sticky top-0 z-30 -mx-4 border-b border-ink-800 bg-ink-950/95 px-4 py-2.5 backdrop-blur safe-top">
      <div className="flex items-center justify-between">
        <p className="min-w-0 truncate text-sm font-semibold text-ink-100">
          {fixture.home_team} <span className="text-ink-500">v</span> {fixture.away_team}
        </p>
        <div className="flex flex-none items-center gap-2">
          <span className="tabular font-mono text-base font-semibold text-ink-100">
            {fixture.home_score}–{fixture.away_score}
          </span>
          {clock && (
            <span
              className={`tabular flex items-center gap-1 rounded-full px-2 py-0.5 font-mono text-xs font-semibold ${
                isLive ? "bg-lose/20 text-lose" : "bg-ink-700 text-ink-300"
              }`}
            >
              {isLive && <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-lose" />}
              {clock}
            </span>
          )}
        </div>
      </div>
      <p className="mt-0.5 text-[11px] text-ink-500">{fixture.competition}</p>
    </div>
  );
}
