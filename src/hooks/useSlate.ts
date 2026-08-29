"use client";

import { useEffect, useState } from "react";
import { supabaseBrowser } from "@/lib/supabase/client";
import { getCurrentSlate, getSlateHistory } from "@/lib/queries";
import type { Slate, SlateEntry } from "@/lib/types";

export function useSlate(groupId: string) {
  const [current, setCurrent] = useState<{ slate: Slate; entries: SlateEntry[] } | null | undefined>(undefined);
  const [history, setHistory] = useState<{ slate: Slate; entries: SlateEntry[] }[] | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const [cur, hist] = await Promise.all([getCurrentSlate(supabaseBrowser, groupId), getSlateHistory(supabaseBrowser, groupId)]);
        if (!cancelled) {
          setCurrent(cur);
          setHistory(hist);
        }
      } catch {
        // keep previous state
      }
    }
    load();

    const channel = supabaseBrowser
      .channel(`slate:${groupId}`)
      .on("postgres_changes", { event: "*", schema: "public", table: "slates" }, load)
      .on("postgres_changes", { event: "*", schema: "public", table: "slate_entries" }, load)
      .on("postgres_changes", { event: "*", schema: "public", table: "coupons" }, load)
      .on("postgres_changes", { event: "*", schema: "public", table: "legs" }, load)
      .subscribe();

    return () => {
      cancelled = true;
      supabaseBrowser.removeChannel(channel);
    };
  }, [groupId]);

  return { current, history };
}
