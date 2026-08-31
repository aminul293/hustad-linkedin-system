-- Hustad LinkedIn Desk: real backing store.
--
-- Two tables. send_log mirrors the console's per-touch state that today lives only in
-- localStorage; content_log mirrors the Posts / Newsletter / Articles tick state. Both are
-- append/update only from the desk page itself (via pipeline/build_desk.py's Supabase hooks) --
-- nothing here is written by a server process, on purpose: this is the minimum real store, not a
-- redesign of the pipeline.
--
-- Run this once in the Supabase SQL editor (Project > SQL Editor > New query) against a fresh
-- project. See backend/db/README.md for the rest of the setup.

create extension if not exists pgcrypto;

-- ---------------------------------------------------------------------------------------------
-- send_log: one row per (target, touch). Mirrors state.entries in the page's own state object.
-- ---------------------------------------------------------------------------------------------
create table if not exists send_log (
  id            uuid primary key default gen_random_uuid(),
  target_id     text        not null,
  touch         smallint    not null,
  send_date     date,
  name          text,
  company       text,
  status        text        not null default 'pending'
                  check (status in ('pending', 'sent', 'replied', 'skipped')),
  sent_at       timestamptz,
  opener        text,                       -- 'standard' | 'shared history' | 'storm trigger'
  past_employer text,
  note          text,
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now(),
  unique (target_id, touch)
);

create index if not exists send_log_send_date_idx on send_log (send_date);
create index if not exists send_log_status_idx on send_log (status);

-- ---------------------------------------------------------------------------------------------
-- content_log: one row per calendar item (a post id like "C-0901", a newsletter issue, an
-- article). Mirrors state.content in the same page.
-- ---------------------------------------------------------------------------------------------
create table if not exists content_log (
  content_id text primary key,
  done       boolean not null default false,
  at         timestamptz,
  status     text,                          -- free text: matches whatever the tab's status field holds
  note       text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- ---------------------------------------------------------------------------------------------
-- updated_at maintains itself; the page never has to set it.
-- ---------------------------------------------------------------------------------------------
create or replace function touch_updated_at() returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

drop trigger if exists send_log_touch_updated_at on send_log;
create trigger send_log_touch_updated_at before update on send_log
  for each row execute function touch_updated_at();

drop trigger if exists content_log_touch_updated_at on content_log;
create trigger content_log_touch_updated_at before update on content_log
  for each row execute function touch_updated_at();

-- ---------------------------------------------------------------------------------------------
-- Access control. This is a single-tenant, one-team tool: nobody signs up, only people you
-- explicitly invite through Supabase Auth can read or write anything. Public sign-ups must be
-- turned off in the dashboard (Authentication > Providers > Email > "Allow new users to sign up"
-- = off) -- RLS alone does not stop someone from creating an account if sign-ups are open.
-- ---------------------------------------------------------------------------------------------
alter table send_log enable row level security;
alter table content_log enable row level security;

drop policy if exists send_log_authenticated_all on send_log;
create policy send_log_authenticated_all on send_log
  for all
  to authenticated
  using (true)
  with check (true);

drop policy if exists content_log_authenticated_all on content_log;
create policy content_log_authenticated_all on content_log
  for all
  to authenticated
  using (true)
  with check (true);

-- No policy at all exists for the anon role, so an unauthenticated request -- including someone
-- who merely has the page's URL and the public anon key, which ships inside the page's own
-- source -- reads and writes nothing. Signing in is what unlocks the tables, not knowing the key.
