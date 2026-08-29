export default function Avatar({
  initials,
  size = "md",
  ring = false,
}: {
  initials: string;
  size?: "sm" | "md";
  ring?: boolean;
}) {
  const dims = size === "sm" ? "h-6 w-6 text-[10px]" : "h-8 w-8 text-xs";
  return (
    <span
      className={`flex ${dims} flex-none items-center justify-center rounded-full bg-ink-700 font-mono font-semibold text-ink-100 ${
        ring ? "ring-2 ring-ink-950" : ""
      }`}
    >
      {initials}
    </span>
  );
}
