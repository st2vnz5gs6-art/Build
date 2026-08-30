"use client";

import { useEffect, useState } from "react";
import { GroupProvider } from "@/lib/GroupContext";
import { getLocalMember, type LocalMember } from "@/lib/member";
import NameEntry from "./NameEntry";
import BottomNav from "./BottomNav";

export default function GroupShell({
  groupId,
  groupCode,
  groupName,
  children,
}: {
  groupId: string;
  groupCode: string;
  groupName: string;
  children: React.ReactNode;
}) {
  // Start undefined on both server and client so the first hydrated render
  // always matches (localStorage doesn't exist server-side) — only after
  // mount do we check for a stored member, avoiding a hydration mismatch.
  const [member, setMember] = useState<LocalMember | null | undefined>(undefined);

  useEffect(() => {
    setMember(getLocalMember(groupCode));
  }, [groupCode]);

  if (member === undefined) return null;

  if (!member) {
    return <NameEntry groupCode={groupCode} groupName={groupName} onJoined={setMember} />;
  }

  return (
    <GroupProvider value={{ groupId, groupCode, groupName, member }}>
      <div className="pb-20">{children}</div>
      <BottomNav groupCode={groupCode} />
    </GroupProvider>
  );
}
