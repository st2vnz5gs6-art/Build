"use client";

import Link from "next/link";
import { useGroup } from "@/lib/GroupContext";
import { useSlate } from "@/hooks/useSlate";
import Avatar from "@/components/Avatar";
import LegRow from "@/components/LegRow";
import { couponUnits, formatUnits } from "@/lib/odds";
import { formatKickoff } from "@/lib/time";
import type { SlateEntry } from "@/lib/types";

export default function SlatePage() {
  const { groupId, groupCode, member } = useGroup();
  const { current, history } = useSlate(groupId);

  const myEntry = current?.entries.find((e) => e.member_id === member.memberId);
  const canEnter = current?.slate.status === "upcoming" && !myEntry;

  return (
    <div className="mx-auto max-w-lg px-4 pt-6 safe-top">
      <header className="mb-1">
        <h1 className="font-display text-3xl uppercase tracking-wide text-ink-100">Slate</h1>
        <p className="text-xs text-ink-400">One coupon each, three legs max, everyone on identical volume.</p>
      </header>

      {current === undefined && <p className="py-12 text-center text-sm text-ink-400">Loading the slate…</p>}

      {current === null && (
        <p className="mt-6 rounded-2xl border border-dashed border-ink-700 p-6 text-center text-sm text-ink-300">
          No slate running right now — check back Tuesday.
        </p>
      )}

      {current && (
        <section className="mt-4">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-ink-200">{current.slate.week_label}</h2>
            <span className="text-xs text-ink-400">
              {current.slate.status === "upcoming" ? `Locks ${formatKickoff(current.slate.locks_at)}` : "Live"}
            </span>
          </div>

          {canEnter && (
            <Link
              href={`/g/${groupCode}/new?slateId=${current.slate.id}`}
              className="mb-4 block w-full rounded-xl bg-accent py-3.5 text-center text-base font-semibold text-white active:scale-[0.98]"
            >
              Enter this week&apos;s slate
            </Link>
          )}

          <div className="space-y-2 pb-2">
            {[...current.entries]
              .sort((a, b) => rank(b) - rank(a))
              .map((entry) => (
                <SlateEntryCard key={entry.id} entry={entry} highlight={entry.member_id === member.memberId} />
              ))}
            {current.entries.length === 0 && <p className="py-6 text-center text-sm text-ink-400">Nobody&apos;s in yet.</p>}
          </div>
        </section>
      )}

      <section className="mt-8 pb-8">
        <h2 className="mb-3 text-sm font-semibold text-ink-200">Past winners</h2>
        <div className="space-y-2">
          {history?.map(({ slate, entries }) => {
            const winner = [...entries].sort((a, b) => rank(b) - rank(a))[0];
            if (!winner) return null;
            return (
              <div key={slate.id} className="flex items-center gap-3 rounded-xl border border-ink-800 bg-ink-900 px-3.5 py-3">
                <Avatar initials={winner.member?.initials ?? "??"} />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm text-ink-100">{winner.member?.name}</p>
                  <p className="text-xs text-ink-400">{slate.week_label}</p>
                </div>
                <span className="tabular font-mono text-sm font-semibold text-win">
                  {formatUnits(winner.coupon ? couponUnits(winner.coupon) : 0)}
                </span>
              </div>
            );
          })}
          {history && history.length === 0 && <p className="text-sm text-ink-400">No history yet — this is week one.</p>}
        </div>
      </section>
    </div>
  );
}

function rank(entry: SlateEntry): number {
  return entry.coupon ? couponUnits(entry.coupon) : -Infinity;
}

function SlateEntryCard({ entry, highlight }: { entry: SlateEntry; highlight: boolean }) {
  const coupon = entry.coupon;
  return (
    <div className={`rounded-xl border px-3.5 py-3 ${highlight ? "border-accent/50 bg-accent-dim/40" : "border-ink-800 bg-ink-900"}`}>
      <div className="mb-2 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Avatar initials={entry.member?.initials ?? "??"} size="sm" />
          <p className="text-sm text-ink-100">{entry.member?.name}</p>
        </div>
        {coupon && (
          <span className={`tabular font-mono text-sm ${coupon.status === "won" ? "text-win" : coupon.status === "lost" ? "text-lose" : "text-ink-300"}`}>
            {formatUnits(couponUnits(coupon))}
          </span>
        )}
      </div>
      <div className="space-y-1.5">{coupon?.legs?.map((leg) => <LegRow key={leg.id} leg={leg} live={coupon.status !== "open"} />)}</div>
    </div>
  );
}
