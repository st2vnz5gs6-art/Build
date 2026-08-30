import type { Market } from "./types";

export type SelectionOption = {
  selection: string;
  label: string;
  /** Suggested decimal odds shown as a fast-tap default; editable. */
  suggestedOdds: number;
};

export type MarketDef = {
  market: Market;
  label: string;
  options: (home: string, away: string) => SelectionOption[];
};

// Only markets the cheap API-Football tier covers reliably. Corners / shots
// on target are deliberately absent — see README "Data feed" section for why,
// and how a new MarketDef slots in later without touching the leg model.
export const MARKETS: MarketDef[] = [
  {
    market: "match_result",
    label: "Match result",
    options: (home, away) => [
      { selection: "home", label: home, suggestedOdds: 1.9 },
      { selection: "draw", label: "Draw", suggestedOdds: 3.4 },
      { selection: "away", label: away, suggestedOdds: 4.2 },
    ],
  },
  {
    market: "double_chance",
    label: "Double chance",
    options: (home, away) => [
      { selection: "home_draw", label: `${home} or draw`, suggestedOdds: 1.3 },
      { selection: "away_draw", label: `${away} or draw`, suggestedOdds: 1.6 },
      { selection: "home_away", label: `${home} or ${away}`, suggestedOdds: 1.25 },
    ],
  },
  {
    market: "over_under",
    label: "Over/Under goals",
    options: () => [
      { selection: "over_1.5", label: "Over 1.5", suggestedOdds: 1.35 },
      { selection: "over_2.5", label: "Over 2.5", suggestedOdds: 1.85 },
      { selection: "over_3.5", label: "Over 3.5", suggestedOdds: 2.7 },
      { selection: "under_2.5", label: "Under 2.5", suggestedOdds: 1.95 },
      { selection: "under_3.5", label: "Under 3.5", suggestedOdds: 1.45 },
    ],
  },
  {
    market: "btts",
    label: "Both teams to score",
    options: () => [
      { selection: "yes", label: "Yes", suggestedOdds: 1.75 },
      { selection: "no", label: "No", suggestedOdds: 2.0 },
    ],
  },
  {
    market: "anytime_scorer",
    label: "Anytime scorer",
    options: () => [{ selection: "player", label: "Pick a player…", suggestedOdds: 3.0 }],
  },
  {
    market: "player_carded",
    label: "Player to be carded",
    options: () => [{ selection: "player", label: "Pick a player…", suggestedOdds: 3.5 }],
  },
  {
    market: "total_cards",
    label: "Total cards",
    options: () => [
      { selection: "over_2.5", label: "Over 2.5 cards", suggestedOdds: 1.9 },
      { selection: "over_3.5", label: "Over 3.5 cards", suggestedOdds: 2.5 },
      { selection: "under_3.5", label: "Under 3.5 cards", suggestedOdds: 1.55 },
    ],
  },
];

export function marketDef(market: Market): MarketDef {
  const def = MARKETS.find((m) => m.market === market);
  if (!def) throw new Error(`unknown market ${market}`);
  return def;
}
