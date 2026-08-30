"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import Link from "next/link";

export default function Home() {
  const router = useRouter();
  const [code, setCode] = useState("");

  function go(e: React.FormEvent) {
    e.preventDefault();
    if (!code.trim()) return;
    router.push(`/g/${code.trim().toUpperCase()}`);
  }

  return (
    <div className="flex min-h-dvh flex-col items-center justify-center gap-10 p-6 safe-top safe-bottom">
      <div className="text-center">
        <p className="font-display text-6xl uppercase tracking-wide text-ink-100">Coupon</p>
        <p className="mt-2 max-w-xs text-sm text-ink-300">
          The pile-on, the live board, the units. No money, just bragging rights.
        </p>
      </div>
      <form onSubmit={go} className="w-full max-w-xs space-y-3">
        <input
          value={code}
          onChange={(e) => setCode(e.target.value)}
          placeholder="Group code"
          maxLength={12}
          autoCapitalize="characters"
          className="w-full rounded-xl border border-ink-700 bg-ink-900 px-4 py-3.5 text-center font-mono text-lg uppercase tracking-[0.3em] text-ink-100 placeholder:tracking-normal placeholder:text-ink-400"
        />
        <button
          type="submit"
          disabled={!code.trim()}
          className="w-full rounded-xl bg-accent py-3.5 text-base font-semibold text-white disabled:opacity-40 active:scale-[0.98]"
        >
          Enter group
        </button>
      </form>
      <p className="text-xs text-ink-500">
        Ask whoever runs your group for the code. New group? They set it up first.
      </p>
      <Link href="/privacy" className="text-xs text-ink-500 underline underline-offset-2">
        Privacy policy
      </Link>
    </div>
  );
}
