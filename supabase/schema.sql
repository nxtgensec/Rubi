create table if not exists public.visitor_daily_counts (
  visit_date date primary key,
  visit_count integer not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.visitor_events (
  id uuid primary key default gen_random_uuid(),
  visit_date date not null,
  visitor_id text not null,
  user_agent text,
  created_at timestamptz not null default now(),
  unique (visit_date, visitor_id)
);

alter table public.visitor_daily_counts enable row level security;
alter table public.visitor_events enable row level security;

drop policy if exists "Allow public read visitor daily counts"
on public.visitor_daily_counts;

create policy "Allow public read visitor daily counts"
on public.visitor_daily_counts
for select
to anon, authenticated
using (true);

drop policy if exists "Service role manages visitor daily counts"
on public.visitor_daily_counts;

create policy "Service role manages visitor daily counts"
on public.visitor_daily_counts
for all
to service_role
using (true)
with check (true);

drop policy if exists "Service role manages visitor events"
on public.visitor_events;

create policy "Service role manages visitor events"
on public.visitor_events
for all
to service_role
using (true)
with check (true);

create table if not exists public.rubi_calls (
  id text primary key,
  provider_call_id text,
  from_number text,
  to_number text,
  created_at timestamptz not null,
  updated_at timestamptz not null default now(),
  call_data jsonb not null
);

create index if not exists rubi_calls_provider_call_id_idx
on public.rubi_calls (provider_call_id);

create index if not exists rubi_calls_created_at_idx
on public.rubi_calls (created_at desc);

alter table public.rubi_calls enable row level security;

drop policy if exists "Service role manages rubi calls"
on public.rubi_calls;

create policy "Service role manages rubi calls"
on public.rubi_calls
for all
to service_role
using (true)
with check (true);
