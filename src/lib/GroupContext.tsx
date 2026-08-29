"use client";

import { createContext, useContext } from "react";
import type { LocalMember } from "./member";

export type GroupContextValue = {
  groupId: string;
  groupCode: string;
  groupName: string;
  member: LocalMember;
};

const GroupContext = createContext<GroupContextValue | null>(null);

export function GroupProvider({ value, children }: { value: GroupContextValue; children: React.ReactNode }) {
  return <GroupContext.Provider value={value}>{children}</GroupContext.Provider>;
}

export function useGroup(): GroupContextValue {
  const ctx = useContext(GroupContext);
  if (!ctx) throw new Error("useGroup must be used within a GroupProvider");
  return ctx;
}
