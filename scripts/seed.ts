/**
 * Seeds one realistic demo group so a fresh deploy isn't empty:
 * - 8 members, a mix of settled + live + upcoming coupons
 * - a live match already in progress (so the Live board has something to show
 *   the moment you open it)
 * - one extra `is_demo` fixture kicking off in a few minutes for `npm run demo`
 *   to take over and simulate at speed
 * - a "this week" Champions League slate plus three weeks of slate history
 *
 * Safe to re-run: it deletes the existing demo group (code TNL8) first.
 */
import { config } from "dotenv";
import { createClient } from "@supabase/supabase-js";
import { combineOdds } from "../src/lib/odds";

// .env.local takes precedence (matches Next.js's own env file loading order);
// dotenv never overwrites a variable that's already set, so this call fills
// in anything .env.local didn't provide.
config({ path: ".env.local" });
config();

const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
const serviceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
if (!url || !serviceKey) {
  console.error("Set NEXT_PUBLIC_SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY before seeding.");
  process.exit(1);
}
const db = createClient(url, serviceKey, { auth: { persistSession: false } });

const GROUP_CODE = "TNL8";
const minutesFromNow = (m: number) => new Date(Date.now() + m * 60_000).toISOString();

async function main() {
  console.log("Clearing existing demo group (if any)...");
  const { data: existing } = await db.from("groups").select("id").eq("code", GROUP_CODE).maybeSingle();
  if (existing) await db.from("groups").delete().eq("id", existing.id);

  console.log("Creating group...");
  const { data: group, error: groupErr } = await db
    .from("groups")
    .insert({ code: GROUP_CODE, name: "Tuesday Night Lads" })
    .select()
    .single();
  if (groupErr || !group) throw groupErr;

  console.log("Adding members...");
  const memberNames = [
    "Jamie Cross",
    "Ollie Banks",
    "Tom Reid",
    "Callum Wray",
    "Ryan Doyle",
    "Josh Farrell",
    "Liam Yates",
    "Dec Sharpe",
  ];
  const initials = (n: string) => {
    const [a, b] = n.split(" ");
    return (a[0] + b[0]).toUpperCase();
  };
  const { data: members, error: memErr } = await db
    .from("members")
    .insert(memberNames.map((name) => ({ group_id: group.id, name, initials: initials(name) })))
    .select();
  if (memErr || !members) throw memErr;
  const m = (name: string) => members.find((x) => x.name === name)!;

  console.log("Creating fixtures...");
  const fixturesToInsert = [
    {
      key: "finished",
      competition: "UEFA Champions League",
      home_team: "Arsenal",
      away_team: "Inter Milan",
      home_short: "ARS",
      away_short: "INT",
      kickoff_at: minutesFromNow(-190),
      status: "finished",
      minute: 90,
      home_score: 2,
      away_score: 1,
      is_demo: false,
    },
    {
      key: "live",
      competition: "UEFA Champions League",
      home_team: "Man City",
      away_team: "Bayern Munich",
      home_short: "MCI",
      away_short: "BAY",
      kickoff_at: minutesFromNow(-63),
      status: "live",
      minute: 63,
      home_score: 1,
      away_score: 1,
      is_demo: false,
    },
    {
      key: "upcoming1",
      competition: "UEFA Champions League",
      home_team: "Real Madrid",
      away_team: "Paris Saint-Germain",
      home_short: "RMA",
      away_short: "PSG",
      kickoff_at: minutesFromNow(40),
      status: "scheduled",
      minute: 0,
      home_score: 0,
      away_score: 0,
      is_demo: false,
    },
    {
      key: "upcoming2",
      competition: "UEFA Champions League",
      home_team: "Liverpool",
      away_team: "Barcelona",
      home_short: "LIV",
      away_short: "BAR",
      kickoff_at: minutesFromNow(130),
      status: "scheduled",
      minute: 0,
      home_score: 0,
      away_score: 0,
      is_demo: false,
    },
    {
      key: "demo",
      competition: "Premier League",
      home_team: "Newcastle",
      away_team: "Aston Villa",
      home_short: "NEW",
      away_short: "AVL",
      kickoff_at: minutesFromNow(3),
      status: "scheduled",
      minute: 0,
      home_score: 0,
      away_score: 0,
      is_demo: true,
    },
    // History fixtures, one per past slate week.
    {
      key: "hist1",
      competition: "UEFA Champions League",
      home_team: "Dortmund",
      away_team: "Juventus",
      home_short: "BVB",
      away_short: "JUV",
      kickoff_at: minutesFromNow(-60 * 24 * 21),
      status: "finished",
      minute: 90,
      home_score: 3,
      away_score: 0,
      is_demo: false,
    },
    {
      key: "hist2",
      competition: "UEFA Champions League",
      home_team: "Atletico Madrid",
      away_team: "Porto",
      home_short: "ATM",
      away_short: "POR",
      kickoff_at: minutesFromNow(-60 * 24 * 14),
      status: "finished",
      minute: 90,
      home_score: 1,
      away_score: 1,
      is_demo: false,
    },
    {
      key: "hist3",
      competition: "UEFA Champions League",
      home_team: "Benfica",
      away_team: "PSV",
      home_short: "BEN",
      away_short: "PSV",
      kickoff_at: minutesFromNow(-60 * 24 * 7),
      status: "finished",
      minute: 90,
      home_score: 2,
      away_score: 2,
      is_demo: false,
    },
  ] as const;

  const { data: fixtures, error: fixErr } = await db
    .from("fixtures")
    .insert(fixturesToInsert.map(({ key, ...f }) => f))
    .select();
  if (fixErr || !fixtures) throw fixErr;
  const fx = (key: (typeof fixturesToInsert)[number]["key"]) =>
    fixtures[fixturesToInsert.findIndex((f) => f.key === key)];

  console.log("Adding fixture events for the finished/live matches...");
  await db.from("fixture_events").insert([
    { fixture_id: fx("finished").id, minute: 12, type: "goal", team: "home", player: "Bukayo Saka" },
    { fixture_id: fx("finished").id, minute: 54, type: "goal", team: "away", player: "Marcus Thuram" },
    { fixture_id: fx("finished").id, minute: 78, type: "goal", team: "home", player: "Kai Havertz" },
    { fixture_id: fx("finished").id, minute: 90, type: "ft" },
    { fixture_id: fx("live").id, minute: 0, type: "kickoff" },
    { fixture_id: fx("live").id, minute: 22, type: "goal", team: "home", player: "Erling Haaland" },
    { fixture_id: fx("live").id, minute: 45, type: "ht" },
    { fixture_id: fx("live").id, minute: 58, type: "card_yellow", team: "away", player: "Joshua Kimmich" },
    { fixture_id: fx("live").id, minute: 61, type: "goal", team: "away", player: "Harry Kane" },
  ]);

  // ---- helper to insert a coupon with legs, copies and correct resolved status ----
  type LegInput = {
    fixtureKey: (typeof fixturesToInsert)[number]["key"];
    market: string;
    selection: string;
    selection_label: string;
    odds: number;
    status: "pending" | "won" | "lost";
  };
  async function makeCoupon(opts: {
    owner: string;
    comment: string;
    legs: LegInput[];
    copiers: string[];
    createdMinutesAgo: number;
  }) {
    const totalOdds = combineOdds(opts.legs.map((l) => l.odds));
    const allScheduled = opts.legs.every((l) => fx(l.fixtureKey).status === "scheduled");
    const anyLost = opts.legs.some((l) => l.status === "lost");
    const allWon = opts.legs.every((l) => l.status === "won");
    const status: "open" | "locked" | "won" | "lost" = allScheduled ? "open" : anyLost ? "lost" : allWon ? "won" : "locked";

    const { data: coupon, error } = await db
      .from("coupons")
      .insert({
        group_id: group!.id,
        owner_id: m(opts.owner).id,
        comment: opts.comment,
        total_odds: totalOdds,
        status,
        locked_at: status === "open" ? null : new Date().toISOString(),
        created_at: minutesFromNow(-opts.createdMinutesAgo),
      })
      .select()
      .single();
    if (error || !coupon) throw error;

    await db.from("legs").insert(
      opts.legs.map((l, i) => ({
        coupon_id: coupon.id,
        fixture_id: fx(l.fixtureKey).id,
        market: l.market,
        selection: l.selection,
        selection_label: l.selection_label,
        odds: l.odds,
        leg_order: i + 1,
        status: l.status,
      }))
    );

    if (opts.copiers.length) {
      await db
        .from("coupon_copies")
        .insert(opts.copiers.map((c) => ({ coupon_id: coupon.id, member_id: m(c).id })));
    }
    return coupon;
  }

  console.log("Creating tonight's coupons (feed + live board)...");

  // Settled coupon from the finished Arsenal game.
  await makeCoupon({
    owner: "Jamie Cross",
    comment: "Arsenal to nick it plus Saka anytime, chalk this on",
    legs: [
      { fixtureKey: "finished", market: "match_result", selection: "home", selection_label: "Arsenal", odds: 1.9, status: "won" },
      { fixtureKey: "finished", market: "anytime_scorer", selection: "player", selection_label: "Saka anytime", odds: 2.6, status: "won" },
    ],
    copiers: ["Ollie Banks", "Tom Reid", "Dec Sharpe"],
    createdMinutesAgo: 210,
  });

  await makeCoupon({
    owner: "Callum Wray",
    comment: "Fancied Inter away, wrong again",
    legs: [
      { fixtureKey: "finished", market: "match_result", selection: "away", selection_label: "Inter Milan", odds: 4.2, status: "lost" },
    ],
    copiers: ["Ryan Doyle"],
    createdMinutesAgo: 205,
  });

  // Live coupon on the Man City game — mid-resolution to show colour coding.
  await makeCoupon({
    owner: "Ryan Doyle",
    comment: "City win to nil was the plan, Kane had other ideas",
    legs: [
      { fixtureKey: "live", market: "match_result", selection: "home", selection_label: "Man City", odds: 1.75, status: "pending" },
      { fixtureKey: "live", market: "btts", selection: "no", selection_label: "BTTS: No", odds: 2.0, status: "lost" },
    ],
    copiers: ["Jamie Cross", "Josh Farrell"],
    createdMinutesAgo: 70,
  });

  await makeCoupon({
    owner: "Liam Yates",
    comment: "Over 2.5 and Haaland to score, easy money",
    legs: [
      { fixtureKey: "live", market: "over_under", selection: "over_2.5", selection_label: "Over 2.5 goals", odds: 1.85, status: "won" },
      { fixtureKey: "live", market: "anytime_scorer", selection: "player", selection_label: "Haaland anytime", odds: 1.65, status: "won" },
    ],
    copiers: ["Jamie Cross", "Tom Reid", "Dec Sharpe", "Josh Farrell"],
    createdMinutesAgo: 68,
  });

  // Upcoming, still copyable (kickoff in the future) — the Feed screen's bread and butter.
  await makeCoupon({
    owner: "Tom Reid",
    comment: "Madrid at home in the CL, does this ever lose",
    legs: [
      { fixtureKey: "upcoming1", market: "match_result", selection: "home", selection_label: "Real Madrid", odds: 1.7, status: "pending" },
      { fixtureKey: "upcoming1", market: "double_chance", selection: "home_draw", selection_label: "Real Madrid or draw", odds: 1.2, status: "pending" },
    ],
    copiers: ["Ollie Banks"],
    createdMinutesAgo: 20,
  });

  await makeCoupon({
    owner: "Dec Sharpe",
    comment: "Liverpool BTTS, on it before kickoff",
    legs: [
      { fixtureKey: "upcoming2", market: "btts", selection: "yes", selection_label: "BTTS: Yes", odds: 1.7, status: "pending" },
    ],
    copiers: [],
    createdMinutesAgo: 8,
  });

  // The demo fixture: a spread of coupons waiting for `npm run demo` to resolve.
  await makeCoupon({
    owner: "Josh Farrell",
    comment: "Newcastle at home, over 2.5, watch this one live",
    legs: [
      { fixtureKey: "demo", market: "match_result", selection: "home", selection_label: "Newcastle", odds: 2.1, status: "pending" },
      { fixtureKey: "demo", market: "over_under", selection: "over_2.5", selection_label: "Over 2.5 goals", odds: 1.9, status: "pending" },
    ],
    copiers: ["Jamie Cross", "Ollie Banks", "Ryan Doyle"],
    createdMinutesAgo: 4,
  });

  await makeCoupon({
    owner: "Ollie Banks",
    comment: "Villa to cause an upset plus BTTS",
    legs: [
      { fixtureKey: "demo", market: "match_result", selection: "away", selection_label: "Aston Villa", odds: 3.6, status: "pending" },
      { fixtureKey: "demo", market: "btts", selection: "yes", selection_label: "BTTS: Yes", odds: 1.75, status: "pending" },
    ],
    copiers: ["Liam Yates"],
    createdMinutesAgo: 3,
  });

  console.log("Creating this week's slate...");
  const { data: currentSlate, error: slateErr } = await db
    .from("slates")
    .insert({
      group_id: group.id,
      week_label: "This week",
      locks_at: fx("live").kickoff_at,
      status: "live",
    })
    .select()
    .single();
  if (slateErr || !currentSlate) throw slateErr;

  const slateEntryOwners: { owner: string; comment: string; legs: LegInput[] }[] = [
    {
      owner: "Jamie Cross",
      comment: "Slate pick: City, then Madrid to follow up",
      legs: [
        { fixtureKey: "live", market: "match_result", selection: "home", selection_label: "Man City", odds: 1.75, status: "pending" },
        { fixtureKey: "upcoming1", market: "match_result", selection: "home", selection_label: "Real Madrid", odds: 1.7, status: "pending" },
      ],
    },
    {
      owner: "Ollie Banks",
      comment: "Slate: Bayern draw no bet feel, plus Liverpool win",
      legs: [
        { fixtureKey: "live", market: "double_chance", selection: "away_draw", selection_label: "Bayern or draw", odds: 1.55, status: "pending" },
        { fixtureKey: "upcoming2", market: "match_result", selection: "home", selection_label: "Liverpool", odds: 1.8, status: "pending" },
      ],
    },
    {
      owner: "Tom Reid",
      comment: "Three legs, going big on the slate",
      legs: [
        { fixtureKey: "live", market: "over_under", selection: "over_2.5", selection_label: "Over 2.5 goals", odds: 1.85, status: "won" },
        { fixtureKey: "upcoming1", market: "match_result", selection: "home", selection_label: "Real Madrid", odds: 1.7, status: "pending" },
        { fixtureKey: "upcoming2", market: "btts", selection: "yes", selection_label: "BTTS: Yes", odds: 1.7, status: "pending" },
      ],
    },
    {
      owner: "Ryan Doyle",
      comment: "Keeping it simple, PSG away",
      legs: [
        { fixtureKey: "upcoming1", market: "match_result", selection: "away", selection_label: "Paris Saint-Germain", odds: 4.5, status: "pending" },
      ],
    },
    {
      owner: "Liam Yates",
      comment: "Slate: Haaland got us started, Barca to cover now",
      legs: [
        { fixtureKey: "live", market: "anytime_scorer", selection: "player", selection_label: "Haaland anytime", odds: 1.65, status: "won" },
        { fixtureKey: "upcoming2", market: "match_result", selection: "away", selection_label: "Barcelona", odds: 4.0, status: "pending" },
      ],
    },
    {
      owner: "Dec Sharpe",
      comment: "Draw specialist, City vs Bayern to share the points",
      legs: [
        { fixtureKey: "live", market: "match_result", selection: "draw", selection_label: "Draw", odds: 3.6, status: "pending" },
      ],
    },
  ];

  for (const entry of slateEntryOwners) {
    const coupon = await makeCoupon({
      owner: entry.owner,
      comment: entry.comment,
      legs: entry.legs,
      copiers: [],
      createdMinutesAgo: 200,
    });
    await db.from("slate_entries").insert({ slate_id: currentSlate.id, member_id: m(entry.owner).id, coupon_id: coupon.id });
  }

  console.log("Creating slate history (3 past weeks)...");
  const history: {
    key: "hist1" | "hist2" | "hist3";
    weekLabel: string;
    entries: { owner: string; legs: LegInput[] }[];
  }[] = [
    {
      key: "hist1",
      weekLabel: "3 weeks ago",
      entries: [
        {
          owner: "Jamie Cross",
          legs: [
            { fixtureKey: "hist1", market: "match_result", selection: "home", selection_label: "Dortmund", odds: 1.6, status: "won" },
            { fixtureKey: "hist1", market: "over_under", selection: "over_2.5", selection_label: "Over 2.5 goals", odds: 1.8, status: "won" },
          ],
        },
        {
          owner: "Ollie Banks",
          legs: [{ fixtureKey: "hist1", market: "match_result", selection: "away", selection_label: "Juventus", odds: 5.0, status: "lost" }],
        },
        {
          owner: "Tom Reid",
          legs: [
            { fixtureKey: "hist1", market: "match_result", selection: "home", selection_label: "Dortmund", odds: 1.6, status: "won" },
            { fixtureKey: "hist1", market: "btts", selection: "no", selection_label: "BTTS: No", odds: 1.7, status: "won" },
            { fixtureKey: "hist1", market: "total_cards", selection: "under_3.5", selection_label: "Under 3.5 cards", odds: 1.5, status: "won" },
          ],
        },
        {
          owner: "Dec Sharpe",
          legs: [{ fixtureKey: "hist1", market: "double_chance", selection: "home_draw", selection_label: "Dortmund or draw", odds: 1.25, status: "won" }],
        },
      ],
    },
    {
      key: "hist2",
      weekLabel: "2 weeks ago",
      entries: [
        {
          owner: "Ryan Doyle",
          legs: [{ fixtureKey: "hist2", market: "match_result", selection: "draw", selection_label: "Draw", odds: 3.3, status: "won" }],
        },
        {
          owner: "Josh Farrell",
          legs: [
            { fixtureKey: "hist2", market: "match_result", selection: "home", selection_label: "Atletico Madrid", odds: 2.0, status: "lost" },
            { fixtureKey: "hist2", market: "btts", selection: "yes", selection_label: "BTTS: Yes", odds: 1.7, status: "won" },
          ],
        },
        {
          owner: "Liam Yates",
          legs: [{ fixtureKey: "hist2", market: "match_result", selection: "away", selection_label: "Porto", odds: 4.0, status: "lost" }],
        },
        {
          owner: "Callum Wray",
          legs: [{ fixtureKey: "hist2", market: "double_chance", selection: "away_draw", selection_label: "Porto or draw", odds: 1.7, status: "won" }],
        },
      ],
    },
    {
      key: "hist3",
      weekLabel: "Last week",
      entries: [
        {
          owner: "Dec Sharpe",
          legs: [
            { fixtureKey: "hist3", market: "btts", selection: "yes", selection_label: "BTTS: Yes", odds: 1.7, status: "won" },
            { fixtureKey: "hist3", market: "over_under", selection: "over_2.5", selection_label: "Over 2.5 goals", odds: 1.8, status: "won" },
            { fixtureKey: "hist3", market: "total_cards", selection: "over_2.5", selection_label: "Over 2.5 cards", odds: 1.9, status: "won" },
          ],
        },
        {
          owner: "Jamie Cross",
          legs: [{ fixtureKey: "hist3", market: "match_result", selection: "home", selection_label: "Benfica", odds: 2.1, status: "lost" }],
        },
        {
          owner: "Ryan Doyle",
          legs: [{ fixtureKey: "hist3", market: "match_result", selection: "away", selection_label: "PSV", odds: 3.5, status: "lost" }],
        },
        {
          owner: "Liam Yates",
          legs: [{ fixtureKey: "hist3", market: "double_chance", selection: "home_away", selection_label: "Benfica or PSV", odds: 1.25, status: "won" }],
        },
      ],
    },
  ];

  for (const week of history) {
    const { data: slate, error } = await db
      .from("slates")
      .insert({
        group_id: group.id,
        week_label: week.weekLabel,
        locks_at: fx(week.key).kickoff_at,
        status: "finished",
      })
      .select()
      .single();
    if (error || !slate) throw error;

    for (const entry of week.entries) {
      const coupon = await makeCoupon({
        owner: entry.owner,
        comment: "Slate entry",
        legs: entry.legs,
        copiers: [],
        createdMinutesAgo: 60 * 24 * 21,
      });
      await db.from("slate_entries").insert({ slate_id: slate.id, member_id: m(entry.owner).id, coupon_id: coupon.id });
    }
  }

  console.log("\nSeed complete.");
  console.log(`Group code: ${GROUP_CODE}`);
  console.log(`Join link:  ${process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000"}/g/${GROUP_CODE}`);
  console.log(`Demo fixture "Newcastle vs Aston Villa" kicks off in ~3 minutes — run "npm run demo" to simulate it live.`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
