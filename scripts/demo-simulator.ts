/**
 * Simulates one match at roughly 2 match-minutes per second so you can watch
 * the Live board resolve without waiting for real football.
 *
 * Run `npm run seed` first — it plants an `is_demo` fixture with a couple of
 * coupons already riding on it. This script finds that fixture, plays out a
 * scripted 90 minutes against it (kickoff, goals, cards, HT, FT), and
 * resolves every leg and coupon attached to it as the match progresses.
 * Every write goes through Supabase, so the app's realtime subscriptions
 * pick it up live — no need to refresh.
 */
import { config } from "dotenv";
import { createClient } from "@supabase/supabase-js";
import { evaluateLeg, recomputeCouponStatus } from "../src/lib/resolve";
import type { FixtureEvent, Leg } from "../src/lib/types";

config({ path: ".env.local" });
config();

const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
const serviceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
if (!url || !serviceKey) {
  console.error("Set NEXT_PUBLIC_SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY before running the demo.");
  process.exit(1);
}
const db = createClient(url, serviceKey, { auth: { persistSession: false } });

const TICK_MS = 500; // 1 match-minute per tick = 2 min/sec

type ScriptedEvent = {
  minute: number;
  type: "goal" | "card_yellow" | "card_red";
  team: "home" | "away";
  player: string;
};

// Scripted so the two demo coupons from seed.ts resolve in an interesting way:
// Newcastle 2-1 Villa, over 2.5 goals lands, both teams score.
const SCRIPT: ScriptedEvent[] = [
  { minute: 8, type: "goal", team: "home", player: "Alexander Isak" },
  { minute: 34, type: "card_yellow", team: "away", player: "John McGinn" },
  { minute: 39, type: "goal", team: "away", player: "Ollie Watkins" },
  { minute: 51, type: "card_yellow", team: "home", player: "Bruno Guimaraes" },
  { minute: 70, type: "goal", team: "home", player: "Anthony Gordon" },
  { minute: 85, type: "card_yellow", team: "away", player: "Emiliano Martinez" },
];

async function main() {
  const { data: fixture, error } = await db
    .from("fixtures")
    .select("*")
    .eq("is_demo", true)
    .neq("status", "finished")
    .order("created_at", { ascending: false })
    .limit(1)
    .maybeSingle();

  if (error) throw error;
  if (!fixture) {
    console.error('No unfinished demo fixture found. Run "npm run seed" first (it creates one, or re-run it for a fresh one).');
    process.exit(1);
  }

  console.log(`Simulating ${fixture.home_team} vs ${fixture.away_team} (fixture ${fixture.id})`);

  let homeScore = 0;
  let awayScore = 0;
  const events: Pick<FixtureEvent, "type" | "player">[] = [];

  await db
    .from("fixtures")
    .update({ status: "live", minute: 0, home_score: 0, away_score: 0, kickoff_at: new Date().toISOString() })
    .eq("id", fixture.id);
  await db.from("fixture_events").insert({ fixture_id: fixture.id, minute: 0, type: "kickoff" });

  async function resolveLegsForFixture(fixtureStatus: "live" | "finished") {
    const { data: legs } = await db.from("legs").select("*").eq("fixture_id", fixture.id).eq("status", "pending");
    if (!legs || legs.length === 0) return;

    const currentFixture = { status: fixtureStatus, home_score: homeScore, away_score: awayScore };
    for (const leg of legs as Leg[]) {
      const newStatus = evaluateLeg(leg, currentFixture, events);
      if (newStatus !== leg.status) {
        await db.from("legs").update({ status: newStatus }).eq("id", leg.id);
        await recomputeCoupon(leg.coupon_id);
      }
    }
  }

  async function recomputeCoupon(couponId: string) {
    const { data: legs } = await db.from("legs").select("status").eq("coupon_id", couponId);
    if (!legs) return;
    const status = recomputeCouponStatus(legs as { status: "pending" | "won" | "lost" }[]);
    await db.from("coupons").update({ status }).eq("id", couponId);
    if (status === "won") {
      const { data: coupon } = await db.from("coupons").select("id, owner_id").eq("id", couponId).single();
      const { data: owner } = coupon ? await db.from("members").select("name").eq("id", coupon.owner_id).single() : { data: null };
      const { count } = await db
        .from("coupon_copies")
        .select("id", { count: "exact", head: true })
        .eq("coupon_id", couponId);
      console.log(`  COUPON LANDED — ${owner?.name ?? "someone"}'s coupon just won (${count ?? 0} on it)`);
    }
  }

  for (let minute = 1; minute <= 90; minute++) {
    await new Promise((r) => setTimeout(r, TICK_MS));

    const due = SCRIPT.filter((e) => e.minute === minute);
    for (const e of due) {
      if (e.type === "goal") {
        if (e.team === "home") homeScore++;
        else awayScore++;
      }
      events.push({ type: e.type, player: e.player });
      await db.from("fixture_events").insert({
        fixture_id: fixture.id,
        minute,
        type: e.type,
        team: e.team,
        player: e.player,
      });
      console.log(`  ${minute}' ${e.type.replace("_", " ")} — ${e.player} (${e.team})`);
    }

    const status = minute === 45 ? "ht" : "live";
    await db
      .from("fixtures")
      .update({ minute, status, home_score: homeScore, away_score: awayScore })
      .eq("id", fixture.id);

    if (minute === 45) {
      await db.from("fixture_events").insert({ fixture_id: fixture.id, minute, type: "ht" });
    }

    await resolveLegsForFixture("live");
  }

  await db.from("fixtures").update({ status: "finished", minute: 90 }).eq("id", fixture.id);
  await db.from("fixture_events").insert({ fixture_id: fixture.id, minute: 90, type: "ft" });
  await resolveLegsForFixture("finished");

  console.log(`\nFull time: ${fixture.home_team} ${homeScore}-${awayScore} ${fixture.away_team}`);
  console.log("Demo simulation complete.");
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
