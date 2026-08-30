import { NextResponse } from "next/server";
import { supabaseServer } from "@/lib/supabase/server";
import { initialsFromName } from "@/lib/member";

export async function POST(req: Request) {
  try {
    const body = await req.json().catch(() => null);
    const groupCode = typeof body?.groupCode === "string" ? body.groupCode.trim().toUpperCase() : "";
    const name = typeof body?.name === "string" ? body.name.trim() : "";

    if (!groupCode || !name) {
      return NextResponse.json({ error: "groupCode and name are required" }, { status: 400 });
    }
    if (name.length > 40) {
      return NextResponse.json({ error: "name is too long" }, { status: 400 });
    }

    const db = supabaseServer();
    const { data: group, error: groupErr } = await db.from("groups").select("id").eq("code", groupCode).maybeSingle();
    if (groupErr) return NextResponse.json({ error: groupErr.message }, { status: 500 });
    if (!group) return NextResponse.json({ error: "unknown group code" }, { status: 404 });

    const { data: member, error } = await db
      .from("members")
      .insert({ group_id: group.id, name, initials: initialsFromName(name) })
      .select()
      .single();

    if (error) return NextResponse.json({ error: error.message }, { status: 500 });
    return NextResponse.json({ member });
  } catch (err) {
    return NextResponse.json({ error: err instanceof Error ? err.message : "unexpected server error" }, { status: 500 });
  }
}
