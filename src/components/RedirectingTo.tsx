"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

/**
 * Renders real content (so OG-scraping bots that don't run JS still see the
 * page's meta tags — see the colocated opengraph-image.tsx) and then hops a
 * real browser on to the destination client-side.
 */
export default function RedirectingTo({ href, label }: { href: string; label: string }) {
  const router = useRouter();

  useEffect(() => {
    router.replace(href);
  }, [href, router]);

  return (
    <div className="flex min-h-dvh flex-col items-center justify-center gap-4 p-6 text-center safe-top safe-bottom">
      <p className="font-display text-3xl uppercase tracking-wide text-ink-100">Coupon</p>
      <p className="text-sm text-ink-300">Opening {label}…</p>
      <a href={href} className="mt-2 rounded-xl bg-accent px-5 py-3 text-sm font-semibold text-white">
        Tap here if it doesn&apos;t open
      </a>
    </div>
  );
}
