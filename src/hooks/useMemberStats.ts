"use client";

import { useEffect, useState } from "react";
import { supabaseBrowser } from "@/lib/supabase/client";
import { getMemberStats } from "@/lib/queries";
import type { MemberStats } from "@/lib/types";

export function useMemberStats(groupId: string) {
  const [stats, setStats] = useState<MemberStats[] | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const data = await getMemberStats(supabaseBrowser, groupId);
        if (!cancelled) setStats(data);
      } catch {
        // keep previous state
      }
    }
    load();

    const channel = supabaseBrowser
      .channel(`stats:${groupId}`)
      .on("postgres_changes", { event: "*", schema: "public", table: "coupons" }, load)
      .subscribe();

    return () => {
      cancelled = true;
      supabaseBrowser.removeChannel(channel);
    };
  }, [groupId]);

  return stats;
}
