"use client";

import { useEffect, useRef, useState } from "react";
import Avatar from "./Avatar";
import { useGroup } from "@/lib/GroupContext";
import type { CouponCopy } from "@/lib/types";

export default function PileOn({
  couponId,
  copies,
  locked,
}: {
  couponId: string;
  copies: CouponCopy[];
  locked: boolean;
}) {
  const { member } = useGroup();
  const [optimisticCopies, setOptimisticCopies] = useState(copies);
  const [busy, setBusy] = useState(false);
  const countRef = useRef(copies.length);
  const [pop, setPop] = useState(false);

  useEffect(() => {
    setOptimisticCopies(copies);
  }, [copies]);

  useEffect(() => {
    if (optimisticCopies.length !== countRef.current) {
      countRef.current = optimisticCopies.length;
      setPop(true);
      const t = setTimeout(() => setPop(false), 320);
      return () => clearTimeout(t);
    }
  }, [optimisticCopies.length]);

  const iAmOn = optimisticCopies.some((c) => c.member_id === member.memberId);
  const shown = optimisticCopies.slice(0, 5);
  const extra = optimisticCopies.length - shown.length;

  async function toggle() {
    if (locked || busy) return;
    setBusy(true);
    const wasOn = iAmOn;
    // optimistic update
    setOptimisticCopies((prev) =>
      wasOn
        ? prev.filter((c) => c.member_id !== member.memberId)
        : [...prev, { id: `optimistic-${Date.now()}`, coupon_id: couponId, member_id: member.memberId, created_at: new Date().toISOString(), member: { id: member.memberId, name: member.name, initials: member.initials, group_id: "", created_at: "" } }]
    );
    try {
      const res = await fetch("/api/copy", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ couponId, memberId: member.memberId }),
      });
      if (!res.ok) throw new Error();
    } catch {
      // revert on failure
      setOptimisticCopies(copies);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex items-center justify-between gap-3">
      <div className="flex items-center gap-2">
        <div className="flex -space-x-2">
          {shown.map((c) => (
            <Avatar key={c.id} initials={c.member?.initials ?? "??"} size="sm" ring />
          ))}
        </div>
        <span className={`tabular text-sm text-ink-300 ${pop ? "animate-pile-pop" : ""}`}>
          {optimisticCopies.length === 0 ? "Be the first on this" : `${optimisticCopies.length}${extra > 0 ? "" : ""} on this`}
        </span>
      </div>
      {!locked && (
        <button
          type="button"
          onClick={toggle}
          disabled={busy}
          className={`rounded-full px-4 py-1.5 text-sm font-semibold transition active:scale-95 ${
            iAmOn ? "bg-accent-dim text-accent-bright" : "bg-accent text-white"
          }`}
        >
          {iAmOn ? "On it" : "Copy"}
        </button>
      )}
    </div>
  );
}
