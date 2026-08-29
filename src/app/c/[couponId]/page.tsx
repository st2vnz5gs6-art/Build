import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { supabaseServerAnon } from "@/lib/supabase/server";
import { getCoupon } from "@/lib/queries";
import RedirectingTo from "@/components/RedirectingTo";

export async function generateMetadata({ params }: { params: { couponId: string } }): Promise<Metadata> {
  const coupon = await getCoupon(supabaseServerAnon(), params.couponId);
  if (!coupon) return { title: "Coupon" };
  const copyCount = coupon.copies?.length ?? 0;
  return {
    title: `${coupon.owner?.name ?? "Someone"}'s coupon — Coupon`,
    description: `${coupon.comment || "A coupon"} · ${copyCount} on it. Open the live board.`,
  };
}

export default async function CouponRedirectPage({ params }: { params: { couponId: string } }) {
  const client = supabaseServerAnon();
  const coupon = await getCoupon(client, params.couponId);
  if (!coupon) notFound();

  const { data: group } = await client.from("groups").select("code").eq("id", coupon.group_id).maybeSingle();
  if (!group) notFound();

  const hasStarted = (coupon.legs ?? []).some((l) => l.fixture && l.fixture.status !== "scheduled");
  const href = hasStarted ? `/g/${group.code}/live` : `/g/${group.code}/feed`;
  return <RedirectingTo href={href} label="the live board" />;
}
