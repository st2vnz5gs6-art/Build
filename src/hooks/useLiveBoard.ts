"use client";

import { useEffect, useState } from "react";
import { supabaseBrowser } from "@/lib/supabase/client";
import { getFeedCoupons, getFixtureEvents, getLiveBoardFixtures } from "@/lib/queries";
import type { Coupon, Fixture, FixtureEvent } from "@/lib/types";

const CACHE_PREFIX = "coupon:cache:live:";

type LiveBoardData = {
  fixtures: Fixture[];
  events: FixtureEvent[];
  coupons: Coupon[];
};

export function useLiveBoard(groupId: string) {
  const [data, setData] = useState<LiveBoardData | null>(() => readCache(groupId));

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const [fixtures, coupons] = await Promise.all([
          getLiveBoardFixtures(supabaseBrowser, groupId),
          getFeedCoupons(supabaseBrowser, groupId),
        ]);
        const events = await getFixtureEvents(
          supabaseBrowser,
          fixtures.map((f) => f.id)
        );
        if (!cancelled) {
          const next = { fixtures, events, coupons };
          setData(next);
          writeCache(groupId, next);
        }
      } catch {
        // keep last known state
      }
    }
    load();

    const channel = supabaseBrowser
      .channel(`live:${groupId}`)
      .on("postgres_changes", { event: "*", schema: "public", table: "fixtures" }, load)
      .on("postgres_changes", { event: "*", schema: "public", table: "fixture_events" }, load)
      .on("postgres_changes", { event: "*", schema: "public", table: "legs" }, load)
      .on("postgres_changes", { event: "*", schema: "public", table: "coupons" }, load)
      .on("postgres_changes", { event: "*", schema: "public", table: "coupon_copies" }, load)
      .subscribe();

    return () => {
      cancelled = true;
      supabaseBrowser.removeChannel(channel);
    };
  }, [groupId]);

  return data;
}

function readCache(groupId: string): LiveBoardData | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(CACHE_PREFIX + groupId);
    return raw ? (JSON.parse(raw) as LiveBoardData) : null;
  } catch {
    return null;
  }
}

function writeCache(groupId: string, data: LiveBoardData) {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(CACHE_PREFIX + groupId, JSON.stringify(data));
  } catch {
    // best-effort
  }
}
