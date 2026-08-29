"use client";

import { Suspense, useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useGroup } from "@/lib/GroupContext";
import { supabaseBrowser } from "@/lib/supabase/client";
import { MARKETS, marketDef, type SelectionOption } from "@/lib/markets";
import { combineOdds, formatOdds, formatUnits, unitsReturn } from "@/lib/odds";
import { formatKickoff } from "@/lib/time";
import type { Fixture, Market } from "@/lib/types";

type LegDraft = {
  fixture: Fixture;
  market: Market;
  selection: string;
  selectionLabel: string;
  odds: number;
};

type Step = "fixture" | "market" | "selection" | "player" | "summary";

export default function NewCouponPage() {
  return (
    <Suspense fallback={null}>
      <NewCouponForm />
    </Suspense>
  );
}

function NewCouponForm() {
  const { groupCode, member } = useGroup();
  const router = useRouter();
  const searchParams = useSearchParams();
  const slateId = searchParams.get("slateId");

  const [fixtures, setFixtures] = useState<Fixture[] | null>(null);
  const [step, setStep] = useState<Step>("fixture");
  const [legs, setLegs] = useState<LegDraft[]>([]);
  const [comment, setComment] = useState("");
  const [pickedFixture, setPickedFixture] = useState<Fixture | null>(null);
  const [pickedMarket, setPickedMarket] = useState<Market | null>(null);
  const [pendingSelection, setPendingSelection] = useState<SelectionOption | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    supabaseBrowser
      .from("fixtures")
      .select("*")
      .eq("status", "scheduled")
      .gt("kickoff_at", new Date().toISOString())
      .order("kickoff_at", { ascending: true })
      .then(({ data }) => setFixtures((data as Fixture[]) ?? []));
  }, []);

  const totalOdds = useMemo(() => combineOdds(legs.map((l) => l.odds)), [legs]);

  function pickFixture(f: Fixture) {
    setPickedFixture(f);
    setStep("market");
  }

  function pickMarket(mk: Market) {
    setPickedMarket(mk);
    setStep("selection");
  }

  function pickSelection(opt: SelectionOption) {
    if (opt.selection === "player") {
      setPendingSelection(opt);
      setStep("player");
      return;
    }
    addLeg(opt.selection, opt.label, opt.suggestedOdds);
  }

  function addLeg(selection: string, label: string, odds: number) {
    if (!pickedFixture || !pickedMarket) return;
    setLegs((prev) => [...prev, { fixture: pickedFixture, market: pickedMarket, selection, selectionLabel: label, odds }]);
    setPickedFixture(null);
    setPickedMarket(null);
    setPendingSelection(null);
    setStep("summary");
  }

  function removeLeg(index: number) {
    setLegs((prev) => prev.filter((_, i) => i !== index));
  }

  function updateLegOdds(index: number, odds: number) {
    setLegs((prev) => prev.map((l, i) => (i === index ? { ...l, odds } : l)));
  }

  function startAnotherLeg() {
    setStep("fixture");
  }

  async function submit() {
    if (legs.length === 0) return;
    setSubmitting(true);
    setError(null);
    try {
      const res = await fetch("/api/coupons", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          groupCode,
          memberId: member.memberId,
          comment,
          slateId: slateId ?? undefined,
          legs: legs.map((l) => ({
            fixtureId: l.fixture.id,
            market: l.market,
            selection: l.selection,
            selectionLabel: l.selectionLabel,
            odds: l.odds,
          })),
        }),
      });
      const json = await res.json();
      if (!res.ok) throw new Error(json.error ?? "couldn't post that coupon");
      router.push(slateId ? `/g/${groupCode}/slate` : `/g/${groupCode}/feed`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "something went wrong");
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto flex min-h-dvh max-w-lg flex-col px-4 pt-6 safe-top safe-bottom">
      <header className="mb-5 flex items-center justify-between">
        <h1 className="font-display text-3xl uppercase tracking-wide text-ink-100">
          {slateId ? "Slate pick" : "New coupon"}
        </h1>
        <button type="button" onClick={() => router.back()} className="text-sm text-ink-400">
          Cancel
        </button>
      </header>

      {legs.length > 0 && step !== "summary" && (
        <p className="mb-4 text-xs text-ink-400">{legs.length}/3 legs added — carry on or go back to review</p>
      )}

      {step === "fixture" && (
        <StepList title="Pick a fixture">
          {fixtures === null && <p className="text-sm text-ink-400">Loading fixtures…</p>}
          {fixtures?.length === 0 && <p className="text-sm text-ink-400">No open fixtures right now.</p>}
          {fixtures?.map((f) => (
            <button
              key={f.id}
              onClick={() => pickFixture(f)}
              className="flex w-full items-center justify-between rounded-xl border border-ink-700 bg-ink-900 px-4 py-3.5 text-left active:scale-[0.99]"
            >
              <span>
                <span className="block text-sm font-medium text-ink-100">
                  {f.home_team} v {f.away_team}
                </span>
                <span className="block text-xs text-ink-400">{f.competition}</span>
              </span>
              <span className="tabular font-mono text-xs text-ink-400">{formatKickoff(f.kickoff_at)}</span>
            </button>
          ))}
        </StepList>
      )}

      {step === "market" && pickedFixture && (
        <StepList title={`${pickedFixture.home_short} v ${pickedFixture.away_short} — pick a market`} onBack={() => setStep("fixture")}>
          {MARKETS.map((mk) => (
            <button
              key={mk.market}
              onClick={() => pickMarket(mk.market)}
              className="w-full rounded-xl border border-ink-700 bg-ink-900 px-4 py-3.5 text-left text-sm font-medium text-ink-100 active:scale-[0.99]"
            >
              {mk.label}
            </button>
          ))}
        </StepList>
      )}

      {step === "selection" && pickedFixture && pickedMarket && (
        <StepList title={marketDef(pickedMarket).label} onBack={() => setStep("market")}>
          {marketDef(pickedMarket)
            .options(pickedFixture.home_team, pickedFixture.away_team)
            .map((opt) => (
              <button
                key={opt.selection}
                onClick={() => pickSelection(opt)}
                className="flex w-full items-center justify-between rounded-xl border border-ink-700 bg-ink-900 px-4 py-3.5 text-left active:scale-[0.99]"
              >
                <span className="text-sm font-medium text-ink-100">{opt.label}</span>
                {opt.selection !== "player" && (
                  <span className="tabular font-mono text-sm text-ink-300">{formatOdds(opt.suggestedOdds)}</span>
                )}
              </button>
            ))}
        </StepList>
      )}

      {step === "player" && pendingSelection && (
        <PlayerNameStep
          marketLabel={pickedMarket ? marketDef(pickedMarket).label : ""}
          suggestedOdds={pendingSelection.suggestedOdds}
          onBack={() => setStep("selection")}
          onConfirm={(name, odds) => addLeg("player", `${name} ${pickedMarket === "player_carded" ? "to be carded" : "anytime"}`, odds)}
        />
      )}

      {step === "summary" && (
        <div className="flex flex-1 flex-col">
          <h2 className="mb-3 text-sm font-medium text-ink-300">Your coupon</h2>
          <div className="space-y-2">
            {legs.map((leg, i) => (
              <div key={i} className="flex items-center gap-2 rounded-xl border border-ink-700 bg-ink-900 px-3 py-2.5">
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm text-ink-100">{leg.selectionLabel}</p>
                  <p className="truncate text-xs text-ink-400">
                    {leg.fixture.home_short} v {leg.fixture.away_short} · {marketDef(leg.market).label}
                  </p>
                </div>
                <input
                  type="number"
                  step="0.01"
                  min="1.01"
                  value={leg.odds}
                  onChange={(e) => updateLegOdds(i, parseFloat(e.target.value) || 1.01)}
                  className="tabular w-16 rounded-lg border border-ink-600 bg-ink-800 px-2 py-1.5 text-right font-mono text-sm text-ink-100"
                />
                <button onClick={() => removeLeg(i)} aria-label="Remove leg" className="text-ink-500">
                  ✕
                </button>
              </div>
            ))}
          </div>

          {legs.length < 3 && (
            <button
              onClick={startAnotherLeg}
              className="mt-3 w-full rounded-xl border border-dashed border-ink-600 py-3 text-sm font-medium text-ink-300 active:scale-[0.99]"
            >
              + Add another leg ({legs.length}/3)
            </button>
          )}

          <div className="mt-5">
            <label htmlFor="comment" className="mb-1.5 block text-sm text-ink-300">
              Say something about it
            </label>
            <input
              id="comment"
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              maxLength={140}
              placeholder="On it before kickoff…"
              className="w-full rounded-xl border border-ink-700 bg-ink-900 px-4 py-3 text-sm text-ink-100 placeholder:text-ink-500"
            />
          </div>

          <div className="mt-4 flex items-baseline justify-between rounded-xl bg-ink-900 px-4 py-3 font-mono">
            <span className="text-xs text-ink-400">Total odds</span>
            <span className="tabular text-base text-ink-100">
              {formatOdds(totalOdds)} <span className="text-accent-bright">{formatUnits(unitsReturn(totalOdds))}</span>
            </span>
          </div>

          {error && <p className="mt-3 text-sm text-lose">{error}</p>}

          <div className="mt-auto pt-6 pb-4">
            <button
              onClick={submit}
              disabled={submitting || legs.length === 0}
              className="w-full rounded-xl bg-accent py-3.5 text-base font-semibold text-white disabled:opacity-40 active:scale-[0.98]"
            >
              {submitting ? "Posting…" : "Post it — locks at kick-off"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function StepList({ title, onBack, children }: { title: string; onBack?: () => void; children: React.ReactNode }) {
  return (
    <div>
      <div className="mb-3 flex items-center gap-2">
        {onBack && (
          <button onClick={onBack} aria-label="Back" className="text-ink-400">
            ←
          </button>
        )}
        <h2 className="text-sm font-medium text-ink-300">{title}</h2>
      </div>
      <div className="space-y-2">{children}</div>
    </div>
  );
}

function PlayerNameStep({
  marketLabel,
  suggestedOdds,
  onBack,
  onConfirm,
}: {
  marketLabel: string;
  suggestedOdds: number;
  onBack: () => void;
  onConfirm: (name: string, odds: number) => void;
}) {
  const [name, setName] = useState("");
  const [odds, setOdds] = useState(suggestedOdds);
  return (
    <div>
      <div className="mb-3 flex items-center gap-2">
        <button onClick={onBack} aria-label="Back" className="text-ink-400">
          ←
        </button>
        <h2 className="text-sm font-medium text-ink-300">{marketLabel}</h2>
      </div>
      <input
        autoFocus
        value={name}
        onChange={(e) => setName(e.target.value)}
        placeholder="Player name"
        className="mb-3 w-full rounded-xl border border-ink-700 bg-ink-900 px-4 py-3 text-sm text-ink-100 placeholder:text-ink-500"
      />
      <div className="mb-4 flex items-center justify-between rounded-xl border border-ink-700 bg-ink-900 px-4 py-3">
        <span className="text-sm text-ink-300">Odds</span>
        <input
          type="number"
          step="0.01"
          min="1.01"
          value={odds}
          onChange={(e) => setOdds(parseFloat(e.target.value) || 1.01)}
          className="tabular w-20 rounded-lg border border-ink-600 bg-ink-800 px-2 py-1.5 text-right font-mono text-sm text-ink-100"
        />
      </div>
      <button
        disabled={!name.trim()}
        onClick={() => onConfirm(name.trim(), odds)}
        className="w-full rounded-xl bg-accent py-3.5 text-base font-semibold text-white disabled:opacity-40"
      >
        Add leg
      </button>
    </div>
  );
}
