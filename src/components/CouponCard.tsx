"use client";

import Avatar from "./Avatar";
import LegRow from "./LegRow";
import PileOn from "./PileOn";
import ShareButton from "./ShareButton";
import type { Coupon } from "@/lib/types";
import { formatOdds, formatUnits, unitsReturn } from "@/lib/odds";
import { formatKickoff } from "@/lib/time";

const CARD_STATUS_CLASS: Record<Coupon["status"], string> = {
  open: "border-ink-700",
  locked: "border-ink-700",
  won: "border-win/70 bg-win/[0.06]",
  lost: "border-ink-800 opacity-60",
  mixed: "border-ink-800 opacity-60",
};

export default function CouponCard({ coupon }: { coupon: Coupon }) {
  const legs = coupon.legs ?? [];
  const copies = coupon.copies ?? [];
  const locked = coupon.status !== "open";
  const earliestKickoff = legs
    .map((l) => l.fixture?.kickoff_at)
    .filter(Boolean)
    .sort()[0];

  return (
    <article className={`rounded-2xl border bg-ink-900 p-4 transition-colors ${CARD_STATUS_CLASS[coupon.status]}`}>
      <header className="mb-3 flex items-start justify-between gap-2">
        <div className="flex items-center gap-2.5">
          <Avatar initials={coupon.owner?.initials ?? "??"} />
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold text-ink-100">{coupon.owner?.name}</p>
            {coupon.comment && <p className="truncate text-sm text-ink-300">{coupon.comment}</p>}
          </div>
        </div>
        <ShareButton couponId={coupon.id} />
      </header>

      <div className="mb-3 space-y-1.5">
        {legs.map((leg) => (
          <LegRow key={leg.id} leg={leg} live={locked} />
        ))}
      </div>

      <div className="mb-3 flex items-baseline justify-between font-mono">
        <span className="tabular text-xs text-ink-400">
          {earliestKickoff ? formatKickoff(earliestKickoff) : ""}
        </span>
        <span className="tabular text-sm text-ink-300">
          {formatOdds(coupon.total_odds)}{" "}
          <span className={coupon.status === "won" ? "text-win" : "text-ink-400"}>
            {formatUnits(coupon.status === "lost" ? -1 : unitsReturn(coupon.total_odds))}
          </span>
        </span>
      </div>

      <PileOn couponId={coupon.id} copies={copies} locked={locked} />
    </article>
  );
}
