"use client";

import { useEffect, useRef, useState } from "react";
import { useGroup } from "@/lib/GroupContext";
import { useLiveBoard } from "@/hooks/useLiveBoard";
import MatchHeader from "@/components/MatchHeader";
import CouponLiveRow from "@/components/CouponLiveRow";
import EventTicker from "@/components/EventTicker";
import CelebrationToast, { type ToastItem } from "@/components/CelebrationToast";
import type { Coupon } from "@/lib/types";

export default function LiveBoardPage() {
  const { groupId } = useGroup();
  const data = useLiveBoard(groupId);
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const seenWon = useRef<Set<string>>(new Set());
  const primed = useRef(false);

  useEffect(() => {
    if (!data) return;
    const wonNow = data.coupons.filter((c) => c.status === "won");

    if (!primed.current) {
      // Don't fire celebrations for coupons that were already settled before this page loaded.
      for (const c of wonNow) seenWon.current.add(c.id);
      primed.current = true;
      return;
    }

    for (const c of wonNow) {
      if (!seenWon.current.has(c.id)) {
        seenWon.current.add(c.id);
        const toast: ToastItem = { id: c.id, ownerName: c.owner?.name ?? "Someone", copyCount: c.copies?.length ?? 0 };
        setToasts((prev) => [...prev, toast]);
        setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== toast.id)), 4000);
      }
    }
  }, [data]);

  if (!data) {
    return <p className="px-4 pt-6 text-center text-sm text-ink-400 safe-top">Loading the board…</p>;
  }

  const liveOrRecent = data.fixtures.filter((f) => f.status !== "scheduled");
  const upcoming = data.fixtures.filter((f) => f.status === "scheduled");

  const couponsByFixture = new Map<string, Coupon[]>();
  for (const coupon of data.coupons) {
    const primaryFixtureId = coupon.legs?.[0]?.fixture_id;
    if (!primaryFixtureId) continue;
    const list = couponsByFixture.get(primaryFixtureId) ?? [];
    list.push(coupon);
    couponsByFixture.set(primaryFixtureId, list);
  }

  return (
    <div className="mx-auto max-w-lg px-4 pt-6 safe-top">
      <CelebrationToast toasts={toasts} />
      <h1 className="mb-4 font-display text-3xl uppercase tracking-wide text-ink-100">Live board</h1>

      <EventTicker events={data.events} fixtures={data.fixtures} />

      {liveOrRecent.length === 0 && upcoming.length === 0 && (
        <p className="py-12 text-center text-sm text-ink-400">No coupons riding on anything tonight yet.</p>
      )}

      <div className="space-y-6 pb-6">
        {liveOrRecent.map((fixture) => (
          <section key={fixture.id}>
            <MatchHeader fixture={fixture} />
            <div className="mt-3 space-y-2">
              {(couponsByFixture.get(fixture.id) ?? []).map((coupon) => (
                <CouponLiveRow key={coupon.id} coupon={coupon} />
              ))}
              {(couponsByFixture.get(fixture.id) ?? []).length === 0 && (
                <p className="py-2 text-center text-xs text-ink-500">No coupons on this one</p>
              )}
            </div>
          </section>
        ))}

        {upcoming.length > 0 && (
          <section>
            <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-ink-500">Kicking off later</h2>
            <div className="space-y-3">
              {upcoming.map((fixture) => (
                <div key={fixture.id} className="rounded-xl border border-ink-800 bg-ink-900/60 px-3.5 py-2.5">
                  <p className="text-sm text-ink-200">
                    {fixture.home_team} v {fixture.away_team}
                  </p>
                  <p className="text-xs text-ink-500">{(couponsByFixture.get(fixture.id) ?? []).length} coupons waiting</p>
                </div>
              ))}
            </div>
          </section>
        )}
      </div>
    </div>
  );
}
