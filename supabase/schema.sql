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

create policy "Allow public read visitor daily counts"
on public.visitor_daily_counts
for select
to anon, authenticated
using (true);

create policy "Service role manages visitor daily counts"
on public.visitor_daily_counts
for all
to service_role
using (true)
with check (true);

create policy "Service role manages visitor events"
on public.visitor_events
for all
to service_role
using (true)
with check (true);
