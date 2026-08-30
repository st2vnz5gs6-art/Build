import { notFound } from "next/navigation";
import { supabaseServerAnon } from "@/lib/supabase/server";
import { getGroupByCode } from "@/lib/queries";
import GroupShell from "@/components/GroupShell";

export default async function GroupLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: { groupCode: string };
}) {
  const group = await getGroupByCode(supabaseServerAnon(), params.groupCode);
  if (!group) notFound();

  return (
    <GroupShell groupId={group.id} groupCode={group.code} groupName={group.name}>
      {children}
    </GroupShell>
  );
}
