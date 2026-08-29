"use client";

import { useState } from "react";

export default function ShareButton({ couponId }: { couponId: string }) {
  const [copied, setCopied] = useState(false);

  async function share() {
    const url = `${window.location.origin}/c/${couponId}`;
    if (navigator.share) {
      try {
        await navigator.share({ url });
        return;
      } catch {
        // fall through to clipboard
      }
    }
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // clipboard denied — nothing more we can do silently
    }
  }

  return (
    <button
      type="button"
      onClick={share}
      aria-label="Share this coupon"
      className="flex h-8 w-8 flex-none items-center justify-center rounded-full text-ink-400 active:scale-95"
    >
      {copied ? (
        <span className="text-[10px] font-semibold text-win">Copied</span>
      ) : (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path
            d="M4 12v6a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-6M16 6l-4-4-4 4M12 2v14"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      )}
    </button>
  );
}
