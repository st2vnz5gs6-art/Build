"use client";

import { useEffect, useRef, useState } from "react";
import { supabaseBrowser } from "@/lib/supabase/client";
import { getFeedCoupons } from "@/lib/queries";
import type { Coupon } from "@/lib/types";

const CACHE_PREFIX = "coupon:cache:feed:";

export function useFeedCoupons(groupId: string) {
  const [coupons, setCoupons] = useState<Coupon[] | null>(() => readCache(groupId));
  const mounted = useRef(true);

  useEffect(() => {
    mounted.current = true;
    let cancelled = false;

    async function load() {
      try {
        const data = await getFeedCoupons(supabaseBrowser, groupId);
        if (!cancelled) {
          setCoupons(data);
          writeCache(groupId, data);
        }
      } catch {
        // keep whatever we already have (cache or previous state)
      }
    }
    load();

    const channel = supabaseBrowser
      .channel(`feed:${groupId}`)
      .on("postgres_changes", { event: "*", schema: "public", table: "coupons" }, load)
      .on("postgres_changes", { event: "*", schema: "public", table: "legs" }, load)
      .on("postgres_changes", { event: "*", schema: "public", table: "coupon_copies" }, load)
      .subscribe();

    return () => {
      cancelled = true;
      mounted.current = false;
      supabaseBrowser.removeChannel(channel);
    };
  }, [groupId]);

  return coupons;
}

function readCache(groupId: string): Coupon[] | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(CACHE_PREFIX + groupId);
    return raw ? (JSON.parse(raw) as Coupon[]) : null;
  } catch {
    return null;
  }
}

function writeCache(groupId: string, data: Coupon[]) {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(CACHE_PREFIX + groupId, JSON.stringify(data));
  } catch {
    // storage full/unavailable — offline cache is best-effort
  }
}
