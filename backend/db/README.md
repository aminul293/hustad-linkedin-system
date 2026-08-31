# The real backing store

What this is: a Postgres database on Supabase, plus two small hooks in `build_desk.py` and
`studio.py` that sync every tick to it. What it replaces: the send log's single point of
failure, which today is whichever browser Eric last used. What it does not replace: the auth
wall in front of the page itself. Read "What this does and does not protect" below before you
ship this -- it matters.

## Setup, in order

**1. Create the project.** [supabase.com](https://supabase.com) &rarr; New project. Free tier is
enough for this volume (a few hundred rows a week). Note the project's region; pick one close to
wherever the page is served from.

**2. Run the schema.** Project &rarr; SQL Editor &rarr; New query &rarr; paste all of
`backend/db/schema.sql` &rarr; Run. It creates `send_log`, `content_log`, and locks both down with
row-level security so only a signed-in user can touch them.

**3. Turn off public sign-ups.** Authentication &rarr; Providers &rarr; Email &rarr; turn off
"Allow new users to sign up." This is the step people skip. RLS restricts tables to the
`authenticated` role, but if anyone can create an account, anyone is `authenticated`.

**4. Invite the one person who should have access.** Authentication &rarr; Users &rarr; Invite
user &rarr; Eric's email. He'll get a magic link the first time; after that the desk page's own
sign-in box (top left, appears automatically once the two secrets below are set) sends him a
fresh one any time his session expires.

**5. Get the two values the page needs.** Project Settings &rarr; API:
- `Project URL` &rarr; this is `SUPABASE_URL`
- `anon` `public` key &rarr; this is `SUPABASE_ANON_KEY`

Both are meant to be public -- the anon key ships inside the page's own HTML source no matter
what, by design. It authorizes *asking* Supabase something; RLS decides whether the answer is
allowed. Never use the `service_role` key here; that one bypasses RLS entirely and must never
reach a browser.

**6. Build with them set.**

```bash
export SUPABASE_URL="https://xxxxxxxx.supabase.co"
export SUPABASE_ANON_KEY="eyJ..."
make site
```

Or pass them as flags instead of env vars: `python3 pipeline/build_desk.py --day 2026-09-08
--supabase-url "$SUPABASE_URL" --supabase-anon-key "$SUPABASE_ANON_KEY" --standalone --out
site/index.html`. Leave both unset and the page behaves exactly as it does today -- this is
additive, not a fork.

**7. In CI / the scheduled rebuild**, set `SUPABASE_URL` and `SUPABASE_ANON_KEY` as repository
secrets (GitHub: Settings &rarr; Secrets and variables &rarr; Actions) so the daily build carries
them without either value sitting in a committed file.

## What changes on the page

A small status line appears under the logo: "not signed in -- writes stay on this device only"
until someone signs in, then "signed in as eric@&hellip;" and "synced to Supabase." A sign-in box
(email + "Send sign-in link") appears the same way. Nothing else about the page changes -- same
five tabs, same cards, same Copy buttons. Ticking Sent, Replied, or a content status now does two
things instead of one: it still writes to `localStorage` immediately (so the page never depends
on being online mid-send), and it also upserts a row to Supabase in the background. On load, if
signed in, the page pulls every row from Supabase and merges it in by whichever copy has the
newer timestamp -- the same merge logic that already reconciles the embedded morning snapshot
against the browser's own copy, just extended to a third source.

## What this does and does not protect

**It does fix:** a second device, or a second person, now sees the same send log the moment a row
changes, instead of it being trapped in one browser. It also fixes the backup problem -- the data
lives in a real database now, not in a weekly CSV someone has to remember to export.

**It does not fix:** the page's HTML still has the full day's queue -- every name, title, company,
drafted message -- baked directly into it as plain JSON, the same way it does today. Signing in
gates the *database*, not the *page*. Anyone who can load the URL at all can view-source it and
read every name on it, signed in or not. That is exactly why auth-in-front-of-the-page (Cloudflare
Access, a host password, whatever `docs/DEPLOY.md` recommends) is still the first thing to do, not
optional now that this exists. This phase and that one solve different problems; do both.
