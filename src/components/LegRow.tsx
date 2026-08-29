import type { Leg } from "@/lib/types";
import { formatOdds } from "@/lib/odds";

const STATUS_STYLES: Record<Leg["status"], string> = {
  pending: "border-pending/60 text-pending",
  won: "border-win/60 text-win",
  lost: "border-lose/60 text-lose",
};

export default function LegRow({ leg, live }: { leg: Leg; live: boolean }) {
  return (
    <div
      className={`flex items-center justify-between gap-2 rounded-lg border-l-2 bg-ink-800/60 px-3 py-2 text-sm ${
        live ? STATUS_STYLES[leg.status] : "border-ink-600 text-ink-200"
      }`}
    >
      <div className="min-w-0">
        <p className="truncate text-ink-100">{leg.selection_label}</p>
        {leg.fixture && (
          <p className="truncate text-xs text-ink-400">
            {leg.fixture.home_short} v {leg.fixture.away_short}
          </p>
        )}
      </div>
      <span className="tabular flex-none font-mono text-xs text-ink-300">{formatOdds(leg.odds)}</span>
    </div>
  );
}
