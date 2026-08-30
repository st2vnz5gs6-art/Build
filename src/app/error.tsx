"use client";

export default function GlobalError({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <div className="flex min-h-dvh flex-col items-center justify-center gap-4 p-6 text-center safe-top safe-bottom">
      <p className="font-display text-3xl uppercase tracking-wide text-ink-100">Dropped the ball</p>
      <p className="max-w-xs text-sm text-ink-300">
        Something went wrong loading that. Could be a dodgy connection — give it another go.
      </p>
      <button type="button" onClick={reset} className="mt-2 rounded-xl bg-accent px-5 py-3 text-sm font-semibold text-white">
        Try again
      </button>
    </div>
  );
}
