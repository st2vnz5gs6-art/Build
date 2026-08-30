import { ImageResponse } from "next/og";
import { supabaseServerAnon } from "@/lib/supabase/server";
import { getCoupon } from "@/lib/queries";
import { formatOdds, formatUnits, unitsReturn } from "@/lib/odds";

export const runtime = "edge";
export const alt = "Coupon";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

const STATUS_COLOR: Record<string, string> = {
  open: "#8a8b92",
  locked: "#f5a623",
  won: "#22c55e",
  lost: "#ef4444",
  mixed: "#ef4444",
};

export default async function Image({ params }: { params: { couponId: string } }) {
  const coupon = await getCoupon(supabaseServerAnon(), params.couponId);

  if (!coupon) {
    return new ImageResponse(
      (
        <div style={{ ...base, alignItems: "center", justifyContent: "center" }}>
          <p style={{ fontSize: 56, color: "#e6e6ea" }}>Coupon</p>
        </div>
      ),
      size
    );
  }

  const legs = coupon.legs ?? [];
  const copyCount = coupon.copies?.length ?? 0;
  const settled = coupon.status !== "open" && coupon.status !== "locked";
  const units = coupon.status === "won" ? unitsReturn(coupon.total_odds) : coupon.status === "lost" ? -1 : unitsReturn(coupon.total_odds);
  const headline =
    coupon.status === "won" ? "LANDED" : coupon.status === "lost" ? "GONE" : coupon.status === "locked" ? "LIVE" : "ON IT";

  return new ImageResponse(
    (
      <div style={base}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <p style={{ fontSize: 32, color: "#5a5b62", letterSpacing: 4, textTransform: "uppercase", margin: 0 }}>Coupon</p>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 12,
              padding: "8px 20px",
              borderRadius: 999,
              background: `${STATUS_COLOR[coupon.status]}22`,
              color: STATUS_COLOR[coupon.status],
              fontSize: 28,
              fontWeight: 700,
              letterSpacing: 2,
            }}
          >
            {headline}
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 20, marginTop: 36 }}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              width: 84,
              height: 84,
              borderRadius: 999,
              background: "#212226",
              color: "#e6e6ea",
              fontSize: 34,
              fontWeight: 700,
            }}
          >
            {coupon.owner?.initials ?? "??"}
          </div>
          <div style={{ display: "flex", flexDirection: "column" }}>
            <p style={{ fontSize: 40, color: "#e6e6ea", margin: 0, fontWeight: 600 }}>{coupon.owner?.name ?? "Someone"}</p>
            {coupon.comment && (
              <p style={{ fontSize: 26, color: "#8a8b92", margin: 0, maxWidth: 760 }}>&ldquo;{coupon.comment}&rdquo;</p>
            )}
          </div>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 14, marginTop: 40 }}>
          {legs.map((leg) => (
            <div
              key={leg.id}
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "18px 26px",
                borderRadius: 16,
                background: "#17181c",
                borderLeft: `6px solid ${settled ? STATUS_COLOR[leg.status] : "#3c3d43"}`,
              }}
            >
              <p style={{ fontSize: 28, color: "#e6e6ea", margin: 0 }}>{leg.selection_label}</p>
              <p style={{ fontSize: 26, color: "#8a8b92", margin: 0, fontFamily: "monospace" }}>{formatOdds(leg.odds)}</p>
            </div>
          ))}
        </div>

        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginTop: "auto" }}>
          <p style={{ fontSize: 30, color: "#b7b8bf", margin: 0 }}>
            {copyCount === 0 ? "Nobody on it yet" : `${copyCount} ${copyCount === 1 ? "person" : "people"} on this`}
          </p>
          <p style={{ fontSize: 44, fontFamily: "monospace", color: units >= 0 ? "#22c55e" : "#ef4444", margin: 0, fontWeight: 700 }}>
            {formatUnits(units)}
          </p>
        </div>
      </div>
    ),
    size
  );
}

const base: React.CSSProperties = {
  width: "100%",
  height: "100%",
  display: "flex",
  flexDirection: "column",
  background: "#0a0b0d",
  padding: "56px 64px",
  fontFamily: "sans-serif",
};
