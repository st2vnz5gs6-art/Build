"use client";

import { useEffect, useState } from "react";
import { confirmAge, hasConfirmedAge } from "@/lib/member";

export default function AgeGate() {
  const [show, setShow] = useState(false);

  useEffect(() => {
    setShow(!hasConfirmedAge());
  }, []);

  if (!show) return null;

  return (
    <div className="fixed inset-0 z-[100] flex flex-col items-center justify-center gap-6 bg-ink-950 p-6 text-center safe-top safe-bottom">
      <div className="max-w-sm space-y-3">
        <p className="font-display text-3xl uppercase tracking-wide text-ink-100">Coupon</p>
        <p className="text-sm text-ink-300">
          This is a private space to track football coupons with your mates in units, not money. No
          real-money betting happens here. You need to be 18 or over to use it.
        </p>
      </div>
      <div className="flex w-full max-w-sm flex-col gap-3">
        <button
          type="button"
          onClick={() => {
            confirmAge();
            setShow(false);
          }}
          className="w-full rounded-xl bg-accent py-3.5 text-base font-semibold text-white active:scale-[0.98]"
        >
          I&apos;m 18 or over
        </button>
        <a
          href="https://www.begambleaware.org"
          className="w-full rounded-xl border border-ink-700 py-3.5 text-center text-base font-semibold text-ink-300"
        >
          I&apos;m under 18, take me away
        </a>
      </div>
    </div>
  );
}
