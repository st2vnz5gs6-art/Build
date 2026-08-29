# Coupon

Turns a private WhatsApp group of football bettors into a shared live experience.
Someone posts a coupon before kick-off, others tap **Copy** to pile on, and once
the match starts everyone watches it resolve together on the live board.

**Units only — no money moves through this app anywhere.** No wallets, no stakes
in pounds, no bookmaker links. That's deliberate: it's what keeps this outside
UK Gambling Commission licensing and App Store real-money-gambling rules.

## Screens

- **Feed** — tonight's coupons, newest first, with the pile-on counter
- **Live board** — every coupon riding on tonight's matches, updating live, with
  a celebration toast when one lands
- **Table** — season units and strike rate per member (reputation, not the contest)
- **Slate** — the weekly Champions League contest: one coupon each, three legs
  max, locked at first kick-off

## Tech stack

- **Next.js 14** (App Router) on Vercel
- **Supabase** — Postgres + Realtime for live leg/score updates
- **Tailwind CSS**
- **next/og** (`ImageResponse`) for dynamic Open Graph share cards
- PWA (installable, offline-ish shell) — no native app, no App Store

## Setup

### 1. Install dependencies

```bash
npm install
```

### 2. Create a Supabase project

Create a project at [supabase.com](https://supabase.com), then run
`supabase/schema.sql` against it — either paste it into the SQL editor, or:

```bash
# with the Supabase CLI, once linked to your project
supabase db push --file supabase/schema.sql
```

This creates every table, the max-3-legs trigger, row level security policies
(public read, writes only via the service-role key — see the comments in the
file), the `member_stats` view backing the Table screen, and enables Realtime
on the tables the app subscribes to.

### 3. Environment variables

Copy `.env.example` to `.env.local` and fill in:

| Variable | Where to get it | Required |
|---|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase → Project Settings → API | Yes |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase → Project Settings → API | Yes |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase → Project Settings → API (keep secret — server-only) | Yes |
| `NEXT_PUBLIC_SITE_URL` | Your deployed URL (`http://localhost:3000` locally) | Yes |
| `API_FOOTBALL_KEY` | [RapidAPI: API-Football](https://rapidapi.com/api-sports/api/api-football) | No — demo mode works without it |
| `API_FOOTBALL_HOST` | Defaults to `api-football-v1.p.rapidapi.com` | No |

### 4. Seed a demo group

```bash
npm run seed
```

Plants one realistic group — **Tuesday Night Lads**, code **`TNL8`** — with 8
members, a finished match, a live match already in progress, two upcoming
fixtures, this week's Champions League slate (6 entries), three weeks of slate
history, and one extra fixture parked for the demo simulator.

Open `http://localhost:3000/g/TNL8`, pick a name, and you're in.

### 5. Run the app

```bash
npm run dev
```

### 6. Watch a match resolve live

```bash
npm run demo
```

Simulates the seeded "Newcastle vs Aston Villa" fixture at roughly 2
match-minutes per second — kickoff, goals, cards, half time, full time — writing
every event straight to Supabase. Leave the Live board open in another tab and
watch it update in real time, no refresh needed. Takes about 45 seconds to run
a full 90 minutes.

Re-run `npm run seed` any time to reset back to a fresh demo state (it's
idempotent — it clears and recreates the `TNL8` group).

## How the pieces fit together

- **No accounts.** Joining a group posts a display name to `/api/members`,
  which creates a row in `members` and hands back an id. That id is stashed in
  `localStorage`, scoped per group code. There's no password, no session — the
  device *is* the identity. Trivially spoofable, which is an accepted tradeoff
  for zero-friction, no-money software.
- **Writes go through API routes**, not the browser directly. The anon key used
  client-side only has read access (RLS policies are `public read`); creating a
  coupon, copying one, or joining a group all hit a Next.js route that uses the
  service-role key server-side, so the "coupons lock at kick-off" and "max 3
  legs" rules are enforced against the actual clock, not just trusted from the
  client. The 3-leg cap is also enforced by a Postgres trigger as a second line
  of defence.
- **Realtime.** Each screen subscribes to the relevant Postgres tables via
  Supabase Realtime and refetches on any change. Simple over clever — group
  sizes here are small (a handful to a few dozen people), so a full refetch per
  change is cheap and a lot easier to reason about than patching state by hand.
- **Offline-ish.** `public/sw.js` caches the app shell so it opens with no
  network. The Feed and Live board additionally cache their last-fetched state
  in `localStorage` and render it immediately on load while a fresh fetch runs
  in the background — so reopening the app on a shaky connection shows the last
  known board instead of a blank screen.
- **Dynamic OG images** (`src/app/c/[couponId]/opengraph-image.tsx` and
  `src/app/g/[groupCode]/opengraph-image.tsx`) are generated server-side with
  `next/og` and reflect live state — leg colours, pile-on count, LANDED/GONE/
  LIVE/ON IT status. This is the growth loop: paste a coupon link into
  WhatsApp and it renders as a rich, current card, not a static screenshot.
  The `/c/[couponId]` and `/g/[groupCode]` pages render real HTML (so link
  previews work) and only redirect a real browser client-side after mount —
  a server-side redirect would return an HTTP 3xx with no meta tags, and most
  chat apps don't unfurl those.

## Data feed & markets

Coupon entry is manual — a three-tap picker (fixture → market → selection,
odds pre-filled and editable) — there's no bet-slip scanning or bookmaker
integration in Phase 1.

Only markets the cheap [API-Football](https://rapidapi.com/api-sports/api/api-football)
tier covers reliably are supported: match result, double chance, over/under
goals, both teams to score, anytime goalscorer, player to be carded, total
cards. Corners and shots on target are deliberately out — that granularity
sits behind the expensive Opta/Sportradar tier. Market resolution logic lives
in one place, `src/lib/resolve.ts` (`evaluateLeg`), so adding a market later —
corners included, once the budget allows a better feed — means adding one
`case` there and one entry to `src/lib/markets.ts`, not touching the leg model.

Live score polling from a real provider isn't wired up in this build (no paid
key is assumed) — `npm run demo` stands in for it by writing directly to the
same tables a poller would, so the whole realtime path is exercised end to
end. Wiring a real 30-second poller means a scheduled job (Vercel Cron or a
small worker) that calls the provider, upserts into `fixtures`/`fixture_events`,
and calls `evaluateLeg` for any `pending` leg on a fixture that changed —
exactly what `scripts/demo-simulator.ts` already does, just from a different
data source.

## Deploying to Vercel

1. Push this repo to GitHub.
2. Import it in Vercel, set the environment variables from step 3 above.
3. Deploy. Then run `npm run seed` locally (pointed at the same Supabase
   project) to populate it, or build your own seed data for a real group.

`npm run demo` is a local/CLI tool, not a Vercel function — it's a long-running
script and Vercel's serverless functions have execution limits, so simulate
matches from your own machine (or a small always-on box) against your deployed
Supabase project. A real live match, via a real data feed, would work the same
way as a scheduled poller instead.

## Known limitations / follow-ups

- `npm audit` still flags two `high` advisories inside Next.js 14.2's bundled
  `postcss` dependency; the fix requires Next 16, a breaking App Router
  migration out of scope for this build — worth revisiting before this holds
  anything more sensitive than group banter.
- Placeholder PWA icons (`scripts/generate-icons.mjs`) — swap
  `public/icons/*.png` for real branding whenever.
- No real-money, no accounts, no OCR, no native app, no push notifications, no
  email, no cross-group leaderboard — all deliberately out per the brief.

## What decides whether this continues

Two groups, four weeks of midweek football, watching for:

1. Do people open the Live board during matches they haven't personally bet
   on? That's the gap between "a product" and "a bet tracker."
2. What share of the group posts a coupon by week four — rising or falling?
3. Does anyone post without being nagged?
