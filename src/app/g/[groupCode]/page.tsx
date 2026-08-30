import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { supabaseServerAnon } from "@/lib/supabase/server";
import { getGroupByCode } from "@/lib/queries";
import RedirectingTo from "@/components/RedirectingTo";

export async function generateMetadata({ params }: { params: { groupCode: string } }): Promise<Metadata> {
  const group = await getGroupByCode(supabaseServerAnon(), params.groupCode);
  if (!group) return { title: "Coupon" };
  return {
    title: `Join ${group.name} — Coupon`,
    description: `You're invited to ${group.name} on Coupon. Pick a name, no account needed.`,
  };
}

export default async function GroupLandingPage({ params }: { params: { groupCode: string } }) {
  const group = await getGroupByCode(supabaseServerAnon(), params.groupCode);
  if (!group) notFound();

  return <RedirectingTo href={`/g/${group.code}/feed`} label={group.name} />;
}
