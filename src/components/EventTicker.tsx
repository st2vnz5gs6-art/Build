import type { Fixture, FixtureEvent } from "@/lib/types";

const EVENT_LABEL: Record<FixtureEvent["type"], string> = {
  kickoff: "Kick off",
  goal: "GOAL",
  card_yellow: "Yellow card",
  card_red: "Red card",
  var: "VAR",
  ht: "Half time",
  ft: "Full time",
};

const EVENT_COLOR: Record<FixtureEvent["type"], string> = {
  kickoff: "text-ink-400",
  goal: "text-win",
  card_yellow: "text-pending",
  card_red: "text-lose",
  var: "text-accent-bright",
  ht: "text-ink-400",
  ft: "text-ink-400",
};

export default function EventTicker({ events, fixtures }: { events: FixtureEvent[]; fixtures: Fixture[] }) {
  const fixtureById = new Map(fixtures.map((f) => [f.id, f]));
  const relevant = events.filter((e) => e.type === "goal" || e.type === "card_red" || e.type === "var").slice(0, 12);

  if (relevant.length === 0) return null;

  return (
    <div className="mb-4 -mx-4 overflow-x-auto border-b border-ink-800 bg-ink-900/60 px-4 py-2">
      <div className="flex gap-4">
        {relevant.map((e) => {
          const fixture = fixtureById.get(e.fixture_id);
          return (
            <div key={e.id} className="flex flex-none items-center gap-1.5 whitespace-nowrap text-xs">
              <span className="tabular font-mono text-ink-500">{e.minute}&apos;</span>
              <span className={`font-semibold ${EVENT_COLOR[e.type]}`}>{EVENT_LABEL[e.type]}</span>
              {e.player && <span className="text-ink-300">{e.player}</span>}
              {fixture && <span className="text-ink-500">{fixture.home_short}-{fixture.away_short}</span>}
            </div>
          );
        })}
      </div>
    </div>
  );
}
