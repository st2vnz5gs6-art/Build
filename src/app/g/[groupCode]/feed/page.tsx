"use client";

import Link from "next/link";
import { useGroup } from "@/lib/GroupContext";
import { useFeedCoupons } from "@/hooks/useFeedCoupons";
import CouponCard from "@/components/CouponCard";

export default function FeedPage() {
  const { groupId, groupCode } = useGroup();
  const coupons = useFeedCoupons(groupId);

  return (
    <div className="mx-auto max-w-lg px-4 pt-6 safe-top">
      <header className="mb-5 flex items-baseline justify-between">
        <h1 className="font-display text-3xl uppercase tracking-wide text-ink-100">Tonight</h1>
        <span className="text-xs text-ink-400">{coupons?.length ?? 0} coupons</span>
      </header>

      {coupons === null && <p className="py-12 text-center text-sm text-ink-400">Loading the feed…</p>}

      {coupons?.length === 0 && (
        <div className="rounded-2xl border border-dashed border-ink-700 p-8 text-center">
          <p className="text-sm text-ink-300">Nobody&apos;s posted yet tonight.</p>
          <Link href={`/g/${groupCode}/new`} className="mt-3 inline-block rounded-xl bg-accent px-5 py-2.5 text-sm font-semibold text-white">
            Post the first one
          </Link>
        </div>
      )}

      <div className="space-y-3 pb-6">
        {coupons?.map((coupon) => (
          <CouponCard key={coupon.id} coupon={coupon} />
        ))}
      </div>
    </div>
  );
}
