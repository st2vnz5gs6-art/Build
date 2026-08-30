import type { SupabaseClient } from "@supabase/supabase-js";
import type { Coupon, Fixture, FixtureEvent, MemberStats, Slate, SlateEntry } from "./types";

const COUPON_SELECT = `
  *,
  owner:members!coupons_owner_id_fkey(*),
  legs(*, fixture:fixtures(*)),
  copies:coupon_copies(*, member:members(*))
`;

export async function getGroupByCode(client: SupabaseClient, code: string) {
  const { data, error } = await client.from("groups").select("*").eq("code", code.toUpperCase()).maybeSingle();
  if (error) throw error;
  return data;
}

export async function getFeedCoupons(client: SupabaseClient, groupId: string): Promise<Coupon[]> {
  const { data, error } = await client
    .from("coupons")
    .select(COUPON_SELECT)
    .eq("group_id", groupId)
    .order("created_at", { ascending: false });
  if (error) throw error;
  return sortLegs((data as unknown as Coupon[]) ?? []);
}

export async function getCoupon(client: SupabaseClient, couponId: string): Promise<Coupon | null> {
  const { data, error } = await client.from("coupons").select(COUPON_SELECT).eq("id", couponId).maybeSingle();
  if (error) throw error;
  const rows = sortLegs(data ? [data as unknown as Coupon] : []);
  return rows[0] ?? null;
}

function sortLegs(coupons: Coupon[]): Coupon[] {
  for (const c of coupons) {
    c.legs?.sort((a, b) => a.leg_order - b.leg_order);
  }
  return coupons;
}

export async function getMemberStats(client: SupabaseClient, groupId: string): Promise<MemberStats[]> {
  const { data, error } = await client
    .from("member_stats")
    .select("*")
    .eq("group_id", groupId)
    .order("units_net", { ascending: false });
  if (error) throw error;
  return (data as MemberStats[]) ?? [];
}

export async function getLiveBoardFixtures(client: SupabaseClient, groupId: string): Promise<Fixture[]> {
  const { data: legRows, error } = await client
    .from("legs")
    .select("fixture:fixtures(*), coupon:coupons!inner(group_id)")
    .eq("coupon.group_id", groupId);
  if (error) throw error;
  const seen = new Map<string, Fixture>();
  for (const row of (legRows as unknown as { fixture: Fixture }[]) ?? []) {
    if (row.fixture) seen.set(row.fixture.id, row.fixture);
  }
  return [...seen.values()].sort((a, b) => new Date(a.kickoff_at).getTime() - new Date(b.kickoff_at).getTime());
}

export async function getFixtureEvents(client: SupabaseClient, fixtureIds: string[]): Promise<FixtureEvent[]> {
  if (fixtureIds.length === 0) return [];
  const { data, error } = await client
    .from("fixture_events")
    .select("*")
    .in("fixture_id", fixtureIds)
    .order("created_at", { ascending: false });
  if (error) throw error;
  return (data as FixtureEvent[]) ?? [];
}

export async function getCurrentSlate(client: SupabaseClient, groupId: string): Promise<{ slate: Slate; entries: SlateEntry[] } | null> {
  const { data: slate, error } = await client
    .from("slates")
    .select("*")
    .eq("group_id", groupId)
    .in("status", ["live", "upcoming"])
    .order("created_at", { ascending: false })
    .limit(1)
    .maybeSingle();
  if (error) throw error;
  if (!slate) return null;

  const { data: entries, error: entriesErr } = await client
    .from("slate_entries")
    .select(`*, member:members(*), coupon:coupons(${COUPON_SELECT})`)
    .eq("slate_id", slate.id);
  if (entriesErr) throw entriesErr;

  return { slate: slate as Slate, entries: (entries as unknown as SlateEntry[]) ?? [] };
}

export async function getSlateHistory(client: SupabaseClient, groupId: string): Promise<{ slate: Slate; entries: SlateEntry[] }[]> {
  const { data: slates, error } = await client
    .from("slates")
    .select("*")
    .eq("group_id", groupId)
    .eq("status", "finished")
    .order("created_at", { ascending: false });
  if (error) throw error;
  const list = (slates as Slate[]) ?? [];

  const results: { slate: Slate; entries: SlateEntry[] }[] = [];
  for (const slate of list) {
    const { data: entries, error: entriesErr } = await client
      .from("slate_entries")
      .select(`*, member:members(*), coupon:coupons(${COUPON_SELECT})`)
      .eq("slate_id", slate.id);
    if (entriesErr) throw entriesErr;
    results.push({ slate, entries: (entries as unknown as SlateEntry[]) ?? [] });
  }
  return results;
}
