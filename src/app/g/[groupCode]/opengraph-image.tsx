import { ImageResponse } from "next/og";
import { supabaseServerAnon } from "@/lib/supabase/server";
import { getGroupByCode } from "@/lib/queries";

export const runtime = "edge";
export const alt = "Join a Coupon group";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default async function Image({ params }: { params: { groupCode: string } }) {
  const client = supabaseServerAnon();
  const group = await getGroupByCode(client, params.groupCode);
  const memberCount = group
    ? (await client.from("members").select("id", { count: "exact", head: true }).eq("group_id", group.id)).count ?? 0
    : 0;

  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          background: "#0a0b0d",
          padding: 64,
        }}
      >
        <p style={{ fontSize: 30, color: "#5a5b62", letterSpacing: 6, textTransform: "uppercase", margin: 0 }}>
          You&apos;re invited to
        </p>
        <p style={{ fontSize: 92, color: "#e6e6ea", fontWeight: 700, margin: "16px 0", textAlign: "center" }}>
          {group?.name ?? "a Coupon group"}
        </p>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 16,
            marginTop: 24,
            padding: "16px 32px",
            borderRadius: 999,
            background: "#17181c",
          }}
        >
          <span style={{ fontSize: 28, color: "#8a8b92" }}>{memberCount} already in</span>
          <span style={{ fontSize: 28, color: "#3c3d43" }}>·</span>
          <span style={{ fontSize: 28, color: "#4f7cff", fontFamily: "monospace", letterSpacing: 4 }}>
            {group?.code ?? params.groupCode.toUpperCase()}
          </span>
        </div>
        <p style={{ fontSize: 26, color: "#5a5b62", marginTop: 40 }}>Tap to join — pick a name, no account needed</p>
      </div>
    ),
    size
  );
}
