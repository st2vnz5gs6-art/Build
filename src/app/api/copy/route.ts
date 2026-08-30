import { NextResponse } from "next/server";
import { supabaseServer } from "@/lib/supabase/server";

// Toggle: copy if not already on it, un-copy if already on it. Only allowed
// while the coupon is still open (pre-kickoff) — copying a locked coupon
// would be pretending you called it before the fact.
export async function POST(req: Request) {
  const body = await req.json().catch(() => null);
  const couponId = typeof body?.couponId === "string" ? body.couponId : "";
  const memberId = typeof body?.memberId === "string" ? body.memberId : "";
  if (!couponId || !memberId) {
    return NextResponse.json({ error: "couponId and memberId are required" }, { status: 400 });
  }

  const db = supabaseServer();
  const { data: coupon, error: couponErr } = await db.from("coupons").select("status").eq("id", couponId).maybeSingle();
  if (couponErr) return NextResponse.json({ error: couponErr.message }, { status: 500 });
  if (!coupon) return NextResponse.json({ error: "coupon not found" }, { status: 404 });
  if (coupon.status !== "open") {
    return NextResponse.json({ error: "this coupon is locked, too late to copy it" }, { status: 409 });
  }

  const { data: existing } = await db
    .from("coupon_copies")
    .select("id")
    .eq("coupon_id", couponId)
    .eq("member_id", memberId)
    .maybeSingle();

  if (existing) {
    const { error } = await db.from("coupon_copies").delete().eq("id", existing.id);
    if (error) return NextResponse.json({ error: error.message }, { status: 500 });
    return NextResponse.json({ copied: false });
  }

  const { error } = await db.from("coupon_copies").insert({ coupon_id: couponId, member_id: memberId });
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json({ copied: true });
}
