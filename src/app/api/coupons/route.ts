import { NextResponse } from "next/server";
import { supabaseServer } from "@/lib/supabase/server";
import { combineOdds } from "@/lib/odds";

type LegPayload = {
  fixtureId: string;
  market: string;
  selection: string;
  selectionLabel: string;
  odds: number;
};

export async function POST(req: Request) {
  try {
    return await handlePost(req);
  } catch (err) {
    return NextResponse.json({ error: err instanceof Error ? err.message : "unexpected server error" }, { status: 500 });
  }
}

async function handlePost(req: Request) {
  const body = await req.json().catch(() => null);
  const groupCode = typeof body?.groupCode === "string" ? body.groupCode.trim().toUpperCase() : "";
  const memberId = typeof body?.memberId === "string" ? body.memberId : "";
  const comment = typeof body?.comment === "string" ? body.comment.trim().slice(0, 140) : "";
  const legs = Array.isArray(body?.legs) ? (body.legs as LegPayload[]) : [];
  const slateId = typeof body?.slateId === "string" ? body.slateId : null;

  if (!groupCode || !memberId) {
    return NextResponse.json({ error: "groupCode and memberId are required" }, { status: 400 });
  }
  if (legs.length === 0 || legs.length > 3) {
    return NextResponse.json({ error: "a coupon needs 1 to 3 legs" }, { status: 400 });
  }
  for (const leg of legs) {
    if (!leg.fixtureId || !leg.market || !leg.selection || !leg.selectionLabel || typeof leg.odds !== "number" || leg.odds < 1.01) {
      return NextResponse.json({ error: "each leg needs a fixture, market, selection and odds" }, { status: 400 });
    }
  }

  const db = supabaseServer();

  const { data: group, error: groupErr } = await db.from("groups").select("id").eq("code", groupCode).maybeSingle();
  if (groupErr) return NextResponse.json({ error: groupErr.message }, { status: 500 });
  if (!group) return NextResponse.json({ error: "unknown group code" }, { status: 404 });

  const { data: member, error: memberErr } = await db
    .from("members")
    .select("id")
    .eq("id", memberId)
    .eq("group_id", group.id)
    .maybeSingle();
  if (memberErr) return NextResponse.json({ error: memberErr.message }, { status: 500 });
  if (!member) return NextResponse.json({ error: "member not found in this group" }, { status: 404 });

  const fixtureIds = [...new Set(legs.map((l) => l.fixtureId))];
  const { data: fixtures, error: fixErr } = await db.from("fixtures").select("*").in("id", fixtureIds);
  if (fixErr) return NextResponse.json({ error: fixErr.message }, { status: 500 });
  if (!fixtures || fixtures.length !== fixtureIds.length) {
    return NextResponse.json({ error: "one or more fixtures not found" }, { status: 404 });
  }

  // Coupons lock at kick-off — no posting once a leg's match has started, no exceptions.
  const kickedOff = fixtures.find((f) => f.status !== "scheduled" || new Date(f.kickoff_at).getTime() <= Date.now());
  if (kickedOff) {
    return NextResponse.json(
      { error: `${kickedOff.home_team} vs ${kickedOff.away_team} has already kicked off — too late for this one` },
      { status: 409 }
    );
  }

  if (slateId) {
    const { data: existingEntry } = await db
      .from("slate_entries")
      .select("id")
      .eq("slate_id", slateId)
      .eq("member_id", memberId)
      .maybeSingle();
    if (existingEntry) {
      return NextResponse.json({ error: "you've already got a coupon in this week's slate" }, { status: 409 });
    }
  }

  const totalOdds = combineOdds(legs.map((l) => l.odds));

  const { data: coupon, error: couponErr } = await db
    .from("coupons")
    .insert({ group_id: group.id, owner_id: memberId, comment, total_odds: totalOdds, status: "open" })
    .select()
    .single();
  if (couponErr || !coupon) return NextResponse.json({ error: couponErr?.message ?? "failed to create coupon" }, { status: 500 });

  const { error: legsErr } = await db.from("legs").insert(
    legs.map((l, i) => ({
      coupon_id: coupon.id,
      fixture_id: l.fixtureId,
      market: l.market,
      selection: l.selection,
      selection_label: l.selectionLabel,
      odds: l.odds,
      leg_order: i + 1,
      status: "pending",
    }))
  );
  if (legsErr) {
    await db.from("coupons").delete().eq("id", coupon.id);
    return NextResponse.json({ error: legsErr.message }, { status: 500 });
  }

  if (slateId) {
    const { error: entryErr } = await db
      .from("slate_entries")
      .insert({ slate_id: slateId, member_id: memberId, coupon_id: coupon.id });
    if (entryErr) {
      await db.from("coupons").delete().eq("id", coupon.id);
      return NextResponse.json({ error: entryErr.message }, { status: 500 });
    }
  }

  return NextResponse.json({ coupon });
}
