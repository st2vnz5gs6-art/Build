import Link from "next/link";

export default function NotFound() {
  return (
    <div className="flex min-h-dvh flex-col items-center justify-center gap-4 p-6 text-center safe-top safe-bottom">
      <p className="font-display text-4xl uppercase tracking-wide text-ink-100">Not here</p>
      <p className="max-w-xs text-sm text-ink-300">
        That group code or link doesn&apos;t match anything. Double-check it, or ask whoever sent it.
      </p>
      <Link href="/" className="mt-2 rounded-xl bg-accent px-5 py-3 text-sm font-semibold text-white">
        Back to start
      </Link>
    </div>
  );
}
