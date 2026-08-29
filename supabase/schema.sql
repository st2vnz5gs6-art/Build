-- Coupon — schema
-- Run this once against a fresh Supabase project (SQL editor, or `supabase db push`).
-- Units only. No money, no stakes, no wallets — see leg/coupon design in README.

create extension if not exists "pgcrypto";

-- ---------------------------------------------------------------------------
-- Groups & members. No accounts: a member is just a display name pinned to a
-- localStorage id on the device that created it. The group code is the door.
-- ---------------------------------------------------------------------------

create table groups (
  id uuid primary key default gen_random_uuid(),
  code text unique not null,
  name text not null,
  created_at timestamptz not null default now()
);

create table members (
  id uuid primary key default gen_random_uuid(),
  group_id uuid not null references groups(id) on delete cascade,
  name text not null,
  initials text not null,
  created_at timestamptz not null default now()
);

create index members_group_idx on members(group_id);

-- ---------------------------------------------------------------------------
-- Fixtures & in-match events. Shared across groups — a fixture is a fixture.
-- Populated either by the API-Football poller or the demo simulator.
-- ---------------------------------------------------------------------------

create table fixtures (
  id uuid primary key default gen_random_uuid(),
  external_id text unique, -- API-Football fixture id, null for demo fixtures
  competition text not null,
  home_team text not null,
  away_team text not null,
  home_short text not null,
  away_short text not null,
  kickoff_at timestamptz not null,
  status text not null default 'scheduled' check (status in ('scheduled', 'live', 'ht', 'finished')),
  minute int not null default 0,
  home_score int not null default 0,
  away_score int not null default 0,
  is_demo boolean not null default false,
  created_at timestamptz not null default now()
);

create table fixture_events (
  id uuid primary key default gen_random_uuid(),
  fixture_id uuid not null references fixtures(id) on delete cascade,
  minute int not null,
  type text not null check (type in ('kickoff', 'goal', 'card_yellow', 'card_red', 'var', 'ht', 'ft')),
  team text check (team in ('home', 'away')),
  player text,
  detail text,
  created_at timestamptz not null default now()
);

create index fixture_events_fixture_idx on fixture_events(fixture_id, created_at desc);

-- ---------------------------------------------------------------------------
-- Coupons & legs. A coupon locks the instant its earliest leg kicks off —
-- enforced in the API route, not just the client.
-- ---------------------------------------------------------------------------

create table coupons (
  id uuid primary key default gen_random_uuid(),
  group_id uuid not null references groups(id) on delete cascade,
  owner_id uuid not null references members(id) on delete cascade,
  comment text not null default '',
  total_odds numeric not null,
  status text not null default 'open' check (status in ('open', 'locked', 'won', 'lost', 'mixed')),
  locked_at timestamptz,
  created_at timestamptz not null default now()
);

create index coupons_group_idx on coupons(group_id, created_at desc);

create table legs (
  id uuid primary key default gen_random_uuid(),
  coupon_id uuid not null references coupons(id) on delete cascade,
  fixture_id uuid not null references fixtures(id) on delete cascade,
  market text not null check (
    market in ('match_result', 'double_chance', 'over_under', 'btts', 'anytime_scorer', 'player_carded', 'total_cards')
  ),
  selection text not null,
  selection_label text not null,
  odds numeric not null,
  leg_order int not null check (leg_order between 1 and 3),
  status text not null default 'pending' check (status in ('pending', 'won', 'lost')),
  unique (coupon_id, leg_order)
);

create index legs_coupon_idx on legs(coupon_id);
create index legs_fixture_idx on legs(fixture_id);

-- Enforce max 3 legs per coupon at the database level too.
create or replace function enforce_max_legs() returns trigger as $$
begin
  if (select count(*) from legs where coupon_id = new.coupon_id) >= 3 then
    raise exception 'coupon already has 3 legs';
  end if;
  return new;
end;
$$ language plpgsql;

create trigger legs_max_three
  before insert on legs
  for each row execute function enforce_max_legs();

-- ---------------------------------------------------------------------------
-- Pile-on. "Copy" = a member saying they're on this coupon too.
-- ---------------------------------------------------------------------------

create table coupon_copies (
  id uuid primary key default gen_random_uuid(),
  coupon_id uuid not null references coupons(id) on delete cascade,
  member_id uuid not null references members(id) on delete cascade,
  created_at timestamptz not null default now(),
  unique (coupon_id, member_id)
);

create index coupon_copies_coupon_idx on coupon_copies(coupon_id);

-- ---------------------------------------------------------------------------
-- Weekly slate contest. One coupon per member per slate, enforced by the
-- unique constraint below (and re-checked in the API route).
-- ---------------------------------------------------------------------------

create table slates (
  id uuid primary key default gen_random_uuid(),
  group_id uuid not null references groups(id) on delete cascade,
  week_label text not null,
  locks_at timestamptz not null,
  status text not null default 'upcoming' check (status in ('upcoming', 'live', 'finished')),
  created_at timestamptz not null default now()
);

create table slate_entries (
  id uuid primary key default gen_random_uuid(),
  slate_id uuid not null references slates(id) on delete cascade,
  member_id uuid not null references members(id) on delete cascade,
  coupon_id uuid not null references coupons(id) on delete cascade,
  unique (slate_id, member_id)
);

-- ---------------------------------------------------------------------------
-- Row Level Security. There is no server-verified auth in Phase 1 (localStorage
-- member ids are self-asserted), so writes are only ever performed by API
-- routes using the service-role key, which bypasses RLS. Anon/client access
-- is read-only, scoped by group membership at the application layer (you
-- need a group code or a direct coupon/group id to read anything).
-- ---------------------------------------------------------------------------

alter table groups enable row level security;
alter table members enable row level security;
alter table fixtures enable row level security;
alter table fixture_events enable row level security;
alter table coupons enable row level security;
alter table legs enable row level security;
alter table coupon_copies enable row level security;
alter table slates enable row level security;
alter table slate_entries enable row level security;

create policy "public read groups" on groups for select using (true);
create policy "public read members" on members for select using (true);
create policy "public read fixtures" on fixtures for select using (true);
create policy "public read fixture_events" on fixture_events for select using (true);
create policy "public read coupons" on coupons for select using (true);
create policy "public read legs" on legs for select using (true);
create policy "public read coupon_copies" on coupon_copies for select using (true);
create policy "public read slates" on slates for select using (true);
create policy "public read slate_entries" on slate_entries for select using (true);

-- ---------------------------------------------------------------------------
-- Reputation view for the Table screen: units returned, coupons posted,
-- strike rate, all derived rather than stored redundantly.
-- ---------------------------------------------------------------------------

create or replace view member_stats as
select
  m.id as member_id,
  m.group_id,
  m.name,
  m.initials,
  count(c.id) filter (where c.status in ('won', 'lost', 'mixed')) as coupons_settled,
  count(c.id) as coupons_posted,
  count(c.id) filter (where c.status = 'won') as coupons_won,
  coalesce(sum(case when c.status = 'won' then c.total_odds - 1 else 0 end), 0) as units_won,
  coalesce(sum(case when c.status in ('lost', 'mixed') then -1 else 0 end), 0) as units_lost,
  coalesce(sum(case when c.status = 'won' then c.total_odds - 1 when c.status in ('lost', 'mixed') then -1 else 0 end), 0) as units_net
from members m
left join coupons c on c.owner_id = m.id
group by m.id, m.group_id, m.name, m.initials;

-- Enable realtime on the tables the live board and feed subscribe to.
alter publication supabase_realtime add table legs;
alter publication supabase_realtime add table fixtures;
alter publication supabase_realtime add table fixture_events;
alter publication supabase_realtime add table coupons;
alter publication supabase_realtime add table coupon_copies;
