"use client";

import { useGroup } from "@/lib/GroupContext";
import { useMemberStats } from "@/hooks/useMemberStats";
import Avatar from "@/components/Avatar";
import { formatUnits } from "@/lib/odds";

export default function TablePage() {
  const { groupId, member } = useGroup();
  const stats = useMemberStats(groupId);

  return (
    <div className="mx-auto max-w-lg px-4 pt-6 safe-top">
      <header className="mb-1">
        <h1 className="font-display text-3xl uppercase tracking-wide text-ink-100">Table</h1>
        <p className="text-xs text-ink-400">Season units. Reputation, not the contest — that&apos;s the slate.</p>
      </header>

      {stats === null && <p className="py-12 text-center text-sm text-ink-400">Loading the table…</p>}

      <div className="mt-4 space-y-1.5 pb-6">
        {stats?.map((s, i) => {
          const strikeRate = s.coupons_settled > 0 ? Math.round((s.coupons_won / s.coupons_settled) * 100) : null;
          const isMe = s.member_id === member.memberId;
          return (
            <div
              key={s.member_id}
              className={`flex items-center gap-3 rounded-xl border px-3.5 py-3 ${
                isMe ? "border-accent/50 bg-accent-dim/40" : "border-ink-800 bg-ink-900"
              }`}
            >
              <span className="tabular w-5 flex-none text-center font-mono text-sm text-ink-500">{i + 1}</span>
              <Avatar initials={s.initials} />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-ink-100">{s.name}</p>
                <p className="tabular text-xs text-ink-400">
                  {s.coupons_posted} posted{strikeRate !== null ? ` · ${strikeRate}% strike rate` : ""}
                </p>
              </div>
              <span className={`tabular flex-none font-mono text-base font-semibold ${s.units_net > 0 ? "text-win" : s.units_net < 0 ? "text-lose" : "text-ink-300"}`}>
                {formatUnits(s.units_net)}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
