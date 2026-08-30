import Avatar from "./Avatar";
import type { Coupon } from "@/lib/types";
import { formatUnits, unitsReturn } from "@/lib/odds";

const DOT_STYLES: Record<string, string> = {
  pending: "bg-pending",
  won: "bg-win",
  lost: "bg-lose",
};

const ROW_STATUS_CLASS: Record<Coupon["status"], string> = {
  open: "border-ink-700",
  locked: "border-ink-700",
  won: "border-win bg-win/[0.08]",
  lost: "border-ink-800 opacity-50",
  mixed: "border-ink-800 opacity-50",
};

export default function CouponLiveRow({ coupon }: { coupon: Coupon }) {
  const legs = coupon.legs ?? [];
  const copyCount = coupon.copies?.length ?? 0;

  return (
    <div className={`flex items-center gap-3 rounded-xl border bg-ink-900 px-3 py-2.5 transition-colors ${ROW_STATUS_CLASS[coupon.status]}`}>
      <Avatar initials={coupon.owner?.initials ?? "??"} size="sm" />
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-1.5">
          {legs.map((leg) => (
            <span key={leg.id} className={`h-2 w-2 flex-none rounded-full ${DOT_STYLES[leg.status]}`} title={leg.selection_label} />
          ))}
          <p className="truncate text-sm text-ink-100">{coupon.owner?.name}</p>
        </div>
        <p className="truncate text-xs text-ink-400">{legs.map((l) => l.selection_label).join(" · ")}</p>
      </div>
      <div className="flex-none text-right">
        <p className={`tabular font-mono text-sm ${coupon.status === "won" ? "text-win" : "text-ink-300"}`}>
          {formatUnits(coupon.status === "lost" ? -1 : unitsReturn(coupon.total_odds))}
        </p>
        {copyCount > 0 && <p className="tabular text-[11px] text-ink-500">{copyCount} on it</p>}
      </div>
    </div>
  );
}
