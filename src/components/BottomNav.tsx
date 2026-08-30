"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const TABS = [
  { href: "feed", label: "Feed", icon: FeedIcon },
  { href: "live", label: "Live", icon: LiveIcon },
  { href: "table", label: "Table", icon: TableIcon },
  { href: "slate", label: "Slate", icon: SlateIcon },
];

export default function BottomNav({ groupCode }: { groupCode: string }) {
  const pathname = usePathname();

  return (
    <nav className="fixed inset-x-0 bottom-0 z-40 border-t border-ink-800 bg-ink-950/95 backdrop-blur safe-bottom">
      <div className="mx-auto flex max-w-lg items-center justify-around">
        {TABS.map((tab) => {
          const href = `/g/${groupCode}/${tab.href}`;
          const active = pathname === href;
          const Icon = tab.icon;
          return (
            <Link
              key={tab.href}
              href={href}
              className="flex flex-1 flex-col items-center gap-1 py-2.5 text-[11px] font-medium"
              aria-current={active ? "page" : undefined}
            >
              <Icon className={active ? "text-accent-bright" : "text-ink-400"} />
              <span className={active ? "text-ink-100" : "text-ink-400"}>{tab.label}</span>
            </Link>
          );
        })}
        <Link
          href={`/g/${groupCode}/new`}
          className="flex flex-1 flex-col items-center gap-1 py-2.5 text-[11px] font-medium"
          aria-label="New coupon"
        >
          <span className="flex h-7 w-7 items-center justify-center rounded-full bg-accent text-lg font-bold leading-none text-white">
            +
          </span>
          <span className="text-ink-400">New</span>
        </Link>
      </div>
    </nav>
  );
}

function iconProps(className?: string) {
  return { width: 20, height: 20, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 2, className };
}

function FeedIcon({ className }: { className?: string }) {
  return (
    <svg {...iconProps(className)}>
      <path d="M4 6h16M4 12h16M4 18h10" strokeLinecap="round" />
    </svg>
  );
}
function LiveIcon({ className }: { className?: string }) {
  return (
    <svg {...iconProps(className)}>
      <circle cx="12" cy="12" r="3" fill="currentColor" stroke="none" />
      <path d="M5 12a7 7 0 0 1 7-7M19 12a7 7 0 0 1-7 7" strokeLinecap="round" />
    </svg>
  );
}
function TableIcon({ className }: { className?: string }) {
  return (
    <svg {...iconProps(className)}>
      <rect x="4" y="4" width="16" height="16" rx="2" />
      <path d="M4 10h16M9 10v10" />
    </svg>
  );
}
function SlateIcon({ className }: { className?: string }) {
  return (
    <svg {...iconProps(className)}>
      <path d="M8 4v3M16 4v3M4 9h16" strokeLinecap="round" />
      <rect x="4" y="5" width="16" height="15" rx="2" />
    </svg>
  );
}
