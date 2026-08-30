import type { Metadata, Viewport } from "next";
import { Barlow_Condensed, IBM_Plex_Mono, Inter } from "next/font/google";
import AgeGate from "@/components/AgeGate";
import ServiceWorkerRegister from "@/components/ServiceWorkerRegister";
import "./globals.css";

const display = Barlow_Condensed({
  subsets: ["latin"],
  weight: ["600", "700"],
  variable: "--font-display",
  display: "swap",
});

const mono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["500", "600"],
  variable: "--font-mono",
  display: "swap",
});

const sans = Inter({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-sans",
  display: "swap",
});

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: "Coupon — on it, gone, landed",
  description: "Turn your group chat's coupons into a shared live scoreboard. Units only, never money.",
  manifest: "/manifest.json",
  icons: {
    icon: [{ url: "/icons/icon-192.png", sizes: "192x192", type: "image/png" }],
    apple: [{ url: "/icons/icon-192.png", sizes: "192x192", type: "image/png" }],
  },
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "Coupon",
  },
};

export const viewport: Viewport = {
  themeColor: "#0a0b0d",
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  viewportFit: "cover",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en-GB" className={`${display.variable} ${mono.variable} ${sans.variable}`}>
      <body className="min-h-dvh bg-ink-950 font-sans text-ink-100 antialiased">
        <AgeGate />
        <ServiceWorkerRegister />
        {children}
      </body>
    </html>
  );
}
