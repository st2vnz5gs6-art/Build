export type FixtureStatus = "scheduled" | "live" | "ht" | "finished";

export type Fixture = {
  id: string;
  external_id: string | null;
  competition: string;
  home_team: string;
  away_team: string;
  home_short: string;
  away_short: string;
  kickoff_at: string;
  status: FixtureStatus;
  minute: number;
  home_score: number;
  away_score: number;
  is_demo: boolean;
  created_at: string;
};

export type FixtureEventType = "kickoff" | "goal" | "card_yellow" | "card_red" | "var" | "ht" | "ft";

export type FixtureEvent = {
  id: string;
  fixture_id: string;
  minute: number;
  type: FixtureEventType;
  team: "home" | "away" | null;
  player: string | null;
  detail: string | null;
  created_at: string;
};

export type Market =
  | "match_result"
  | "double_chance"
  | "over_under"
  | "btts"
  | "anytime_scorer"
  | "player_carded"
  | "total_cards";

export type LegStatus = "pending" | "won" | "lost";

export type Leg = {
  id: string;
  coupon_id: string;
  fixture_id: string;
  market: Market;
  selection: string;
  selection_label: string;
  odds: number;
  leg_order: number;
  status: LegStatus;
  fixture?: Fixture;
};

export type CouponStatus = "open" | "locked" | "won" | "lost" | "mixed";

export type Coupon = {
  id: string;
  group_id: string;
  owner_id: string;
  comment: string;
  total_odds: number;
  status: CouponStatus;
  locked_at: string | null;
  created_at: string;
  legs?: Leg[];
  owner?: Member;
  copies?: CouponCopy[];
};

export type Member = {
  id: string;
  group_id: string;
  name: string;
  initials: string;
  created_at: string;
};

export type CouponCopy = {
  id: string;
  coupon_id: string;
  member_id: string;
  created_at: string;
  member?: Member;
};

export type Group = {
  id: string;
  code: string;
  name: string;
  created_at: string;
};

export type SlateStatus = "upcoming" | "live" | "finished";

export type Slate = {
  id: string;
  group_id: string;
  week_label: string;
  locks_at: string;
  status: SlateStatus;
  created_at: string;
};

export type SlateEntry = {
  id: string;
  slate_id: string;
  member_id: string;
  coupon_id: string;
  member?: Member;
  coupon?: Coupon;
};

export type MemberStats = {
  member_id: string;
  group_id: string;
  name: string;
  initials: string;
  coupons_settled: number;
  coupons_posted: number;
  coupons_won: number;
  units_won: number;
  units_lost: number;
  units_net: number;
};

export const MARKET_LABELS: Record<Market, string> = {
  match_result: "Match result",
  double_chance: "Double chance",
  over_under: "Over/Under goals",
  btts: "Both teams to score",
  anytime_scorer: "Anytime scorer",
  player_carded: "Player to be carded",
  total_cards: "Total cards",
};
