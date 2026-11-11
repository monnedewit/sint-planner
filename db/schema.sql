-- Sint-planner: schema (Supabase / Postgres)
create table acties (
  id uuid primary key default gen_random_uuid(),
  naam text not null,
  jaar int not null
);

create table personen (
  id uuid primary key default gen_random_uuid(),
  naam text not null,
  telefoon text,
  rollen text[] not null default '{}',   -- 'sint','chauffeur','piet'
  actief boolean not null default true,
  notitie text
);

create table routes (
  id uuid primary key default gen_random_uuid(),
  actie_id uuid not null references acties(id) on delete cascade,
  datum date not null,
  soort text not null default 'regulier',  -- 'regulier' | 'gezinnen'
  volgorde int not null default 0,
  locatie text,
  plaats text,
  aanwezig_p time, aanwezig_s time, aanwezig_c time,
  vertrek time, terug time, terugkomst time,
  aantal_gezinnen int,                      -- alleen bij soort='gezinnen'
  opmerking text
);

-- Eén regel per benodigde rol per route (S, C1, C2, P1..Pn)
create table plekken (
  id uuid primary key default gen_random_uuid(),
  route_id uuid not null references routes(id) on delete cascade,
  rol text not null check (rol in ('S','C','P')),
  nummer int not null default 1,
  status text not null default 'open'
    check (status in ('open','ingevuld','eigen','niet_nodig')),
  persoon_id uuid references personen(id) on delete set null,
  vrije_tekst text                          -- bv. "vader", "8x eigen"
);

-- Gezinsbezoeken binnen een gezinnenroute (later invullen)
create table gezinnen (
  id uuid primary key default gen_random_uuid(),
  route_id uuid not null references routes(id) on delete cascade,
  volgorde int not null default 0,
  naam text, adres text, plaats text,
  tijd time, aantal_kinderen int, notitie text
);

-- Rechten: iedereen ingelogd mag lezen, alleen planners schrijven
alter table acties enable row level security;
alter table personen enable row level security;
alter table routes enable row level security;
alter table plekken enable row level security;
alter table gezinnen enable row level security;
create table planners (user_id uuid primary key references auth.users(id));
create function is_planner() returns boolean language sql stable as
  $$ select exists (select 1 from planners where user_id = auth.uid()) $$;
do $$ declare t text; begin
  foreach t in array array['acties','personen','routes','plekken','gezinnen'] loop
    execute format('create policy lezen on %I for select to authenticated using (true)', t);
    execute format('create policy schrijven on %I for all to authenticated using (is_planner()) with check (is_planner())', t);
  end loop; end $$;
