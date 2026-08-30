export type ToastItem = { id: string; ownerName: string; copyCount: number };

export default function CelebrationToast({ toasts }: { toasts: ToastItem[] }) {
  if (toasts.length === 0) return null;
  return (
    <div className="pointer-events-none fixed inset-x-0 top-0 z-50 flex flex-col items-center gap-2 p-3 safe-top">
      {toasts.map((t) => (
        <div
          key={t.id}
          className="animate-toast-in flex items-center gap-2 rounded-full border border-win/40 bg-ink-900/95 px-4 py-2.5 shadow-lg shadow-black/40"
        >
          <span className="h-2 w-2 flex-none rounded-full bg-win" />
          <p className="text-sm text-ink-100">
            <span className="font-semibold text-win">{t.ownerName}&apos;s coupon landed</span>
            {t.copyCount > 0 && <span className="text-ink-300"> · {t.copyCount} on it</span>}
          </p>
        </div>
      ))}
    </div>
  );
}
