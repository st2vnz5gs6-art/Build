"use client";

import { useState } from "react";
import { setLocalMember } from "@/lib/member";
import { initialsFromName } from "@/lib/initials";

export default function NameEntry({
  groupCode,
  groupName,
  onJoined,
}: {
  groupCode: string;
  groupName: string;
  onJoined: (member: { memberId: string; name: string; initials: string }) => void;
}) {
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const res = await fetch("/api/members", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ groupCode, name: name.trim() }),
      });
      const json = await res.json();
      if (!res.ok) throw new Error(json.error ?? "couldn't join");
      const member = { memberId: json.member.id as string, name: json.member.name as string, initials: json.member.initials as string };
      setLocalMember(groupCode, member);
      onJoined(member);
    } catch (err) {
      setError(err instanceof Error ? err.message : "something went wrong");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-dvh flex-col items-center justify-center gap-8 p-6 safe-top safe-bottom">
      <div className="text-center">
        <p className="font-display text-2xl uppercase tracking-wide text-ink-300">Joining</p>
        <h1 className="font-display text-4xl uppercase tracking-wide text-ink-100">{groupName}</h1>
      </div>
      <form onSubmit={submit} className="w-full max-w-sm space-y-4">
        <div>
          <label htmlFor="name" className="mb-1.5 block text-sm text-ink-300">
            What should we call you?
          </label>
          <input
            id="name"
            autoFocus
            value={name}
            onChange={(e) => setName(e.target.value)}
            maxLength={40}
            placeholder="Jamie Cross"
            className="w-full rounded-xl border border-ink-700 bg-ink-900 px-4 py-3.5 text-base text-ink-100 placeholder:text-ink-400"
          />
          {name.trim() && (
            <p className="mt-1.5 text-xs text-ink-400">
              Shows as <span className="tabular font-mono text-ink-200">{initialsFromName(name)}</span> on coupons
            </p>
          )}
        </div>
        {error && <p className="text-sm text-lose">{error}</p>}
        <button
          type="submit"
          disabled={busy || !name.trim()}
          className="w-full rounded-xl bg-accent py-3.5 text-base font-semibold text-white disabled:opacity-40 active:scale-[0.98]"
        >
          {busy ? "Joining…" : "Join the group"}
        </button>
      </form>
    </div>
  );
}
