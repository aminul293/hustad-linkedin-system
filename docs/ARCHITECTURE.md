# Architecture

## Data flow

```
data/raw/                             data/work/                      data/out/
─────────                             ──────────                      ─────────
Connections.csv       ─┐
messages.csv           ├─ classify ──► master_contacts.csv ─┐
Invitations.csv        │                                     │
Endorsements.csv      ─┘                                     ├─ scale_plan ─► plan_targets.csv
                                                             │                      │
opportunities_2026.csv ─┬─ active_accounts ─► client map ────┘                      │
data/work/account_map.json ─┘                                                       │
                                                                                    │
pipeline/calendar_ref.csv ── recalendar ────────────────────────────────────────────┤
pipeline/hooks.py         ─┐                                                        │
data/research/*.json      ─┴─ copy_engine ───────────────────► plan_with_copy_final.csv
                                                                                    │
                          ┌─────────────────────────────────────────────────────────┤
                          │                                                         │
data/work/storm_openers.py ─┴─ build_desk ─► desk.html         build_onedrive ─► per-day CSVs
                                                               build_workbook ─► .xlsx
```

## Key files

| File | Role |
|---|---|
| `pipeline/paths.py` | every path in one place; honours `HUSTAD_DATA` |
| `pipeline/classify.py` | loads the export, derives engagement state, scores and tiers, applies gates |
| `pipeline/active_accounts.py` | applies the Gate G2 client map; the map itself is `data/work/account_map.json` |
| `pipeline/hooks.py` | verified per-company opening facts, each traced to a source |
| `pipeline/copy_engine.py` | writes every message; the only source of outreach copy |
| `pipeline/scale_plan.py` | tops the plan up to the daily target under firm caps |
| `pipeline/level_calendar.py` | pushes follow-ups forward so no day exceeds the send cap |
| `pipeline/build_desk.py` | builds the page |
| `pipeline/storm_openers.py` | template only; the live daily file is `data/work/storm_openers.py` |
| `pipeline/reply_engine.py` | 22 reply categories, decision styles, buyer states, objections; renders as the Reply Center tab |
| `pipeline/content_engine.py` | the posting calendar as code: posts, newsletter, articles, all QA gated |
| `pipeline/studio.py` | renders the Posts, Newsletter and Articles tabs and the SVG asset templates |
| `worker/post_scheduler.py` | the only LinkedIn API caller; posts due calendar items, idempotent, dry run default |
| `worker/render_assets.py` | rasterizes graphics to PNG and carousels to PDF for the worker |

## Scoring and gating

Each connection scores out of 100: seniority to 40, function to 30, segment to 12, company class to
12, national scale to 8, recency to 4. Tier 1 is 88 and above and never a site-level role.

Four gates, all fail-closed. A row missing data is blocked and queued with a reason, never sent:

- **G1** provenance recorded
- **G2** not matched to an active client account (that is warm outreach, handled elsewhere)
- **G3** role and company verified within 183 days
- **G4** inside tier caps and channel policy

## The three-touch sequence

Touch 1 on day 0, touch 2 at +7 business days, touch 3 at +14 and at least 7 after touch 2. Any
reply halts the sequence. `level_calendar.py` pushes follow-ups forward when a day would otherwise
exceed the cap, which is what stops the Labor Day pile-up.

## The page is five tabs

`build_desk.py` emits one page: DM Outreach (the desk), Reply Center (reply_engine rendered as a
searchable reference), Posts, Newsletter and Articles (studio panes from the content calendar).
One URL, one bookmark, and the browser storage below carries every tab's state through the daily
rebuild. The content calendar loads work first, sample second, and the three content tabs render
an honest empty state when neither exists, so the outreach build never blocks on content.

## The send log

Lives in `localStorage` on the desk page, keyed `hustad-console-log-v2`, as
`{entries: {"TARGETID|TOUCH": {...}}}`. Browser storage is keyed to the page's origin and survives
republishing to the same URL, which is what lets a scheduled job rebuild the page daily without
touching it.

Entry shape: `{id, touch, date, name, company, done, at, opener, pe, note, reply, ts}` where
`opener` is `standard`, `shared history`, or `storm trigger` and is set from whichever draft tab was
showing when the row was ticked.

The same state object carries `content`, keyed by calendar id (`C-0901`, `NL-1`, `A-01`), holding
`{done, at, status, note, ts}` for posted ticks, newsletter publishes and article statuses. State
version is 4; the merge is per key by newest `ts`, so the embedded seed and this browser's copy
combine instead of clobbering.

## Determinism

Every variant choice keys off `md5(url_key)`, so the same person gets the same message across
rebuilds. This is load-bearing: some of these messages have already been sent, and a rebuild must
not silently reword one that is in somebody's inbox.


## What is code and what is data

The split matters, because the code is meant to be committed and the data never is.

| In git | Not in git, lives in `data/work/` |
|---|---|
| `pipeline/*.py`, the engines and the build | `account_map.json`, Hustad's client roster and the CRM-to-LinkedIn name map |
| `pipeline/hooks.py`, company hooks, no individual named | `research/*.json`, company research that quotes named executives |
| `data/sample/*`, synthetic, including a 3-company research sample | `plan_change_log*.csv`, why each target was removed, by name |
| `pipeline/calendar_ref.csv`, target ids and dates, no names | `storm_openers.py`, today's triggers and verification notes, by name |
| `docs/*`, engineering documentation | `PROGRAM_STATUS.md`, the running record, which names people |
| | `master_contacts.csv`, `plan_targets.csv`, `plan_with_copy_final.csv` |

Every one of those runtime files degrades gracefully. Missing `account_map.json` falls back to the
synthetic sample, missing `storm_openers.py` falls back to an empty template, and a missing plan is
what `make sample` exists to fix. A fresh clone runs; it just runs on invented people.
