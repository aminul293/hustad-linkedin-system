# Notes for Aminul

Handoff for the Hustad LinkedIn system. One page, five tabs, one repo: cold DM outreach, the reply
center, the posting calendar with designed assets, the newsletter, and the article pipeline. This
covers what exists, why it is shaped the way it is, what ships ready to automate, and what to build
next in what order.

Eric works the DM hour by hand every weekday from 11:05 to 12:05 Central, and posts on Tuesday,
Wednesday, Thursday and Saturday. The system's job is to make all of that run from one bookmark
with zero research or bookkeeping inside the block, and to let the posting side go fully automatic
through the official LinkedIn API once you wire two secrets.

## 0. Deploy this week, in order

1. Push the repo (private) and confirm CI is green. CI runs entirely on synthetic data.
2. Serve the page: `make site` produces one self contained `site/index.html`. Put it behind any
   identity check (Cloudflare Access is an afternoon). The Claude artifact version keeps running
   in parallel; nothing breaks if you take a week.
3. Create the LinkedIn app, self serve products only, and set the two secrets
   (docs/API_INTEGRATIONS.md walks it). Flip the `POSTING_ENABLED` repository variable and the
   next Tuesday post publishes itself; the worker dry runs by default until then and is
   idempotent after.
4. Apply for the Community Management API the same day (one to two week review). Until it lands,
   Wednesday company posts are a two minute manual step from the Posts tab.
5. Newsletters, articles and every DM stay human. That is platform reality and program rule, not
   backlog.

---

## 1. What it does, end to end

```
LinkedIn export + CRM opportunity export
        │
        ▼
  classify.py ──────────► master_contacts.csv
        │                 4,839 connections scored, tiered, gated
        ▼
  scale_plan.py ────────► plan_targets.csv
        │                 1,424 primaries at 40 first touches a weekday
        ▼
  recalendar.py ────────► dates pinned from calendar_ref.csv
        ▼
  copy_engine.py ───────► plan_with_copy_final.csv
        │                 every message written and linted
        ▼
  level_calendar.py ────► no day over the send cap
        │
        ├──► build_desk.py ──────► the page Eric works from
        ├──► build_onedrive.py ──► per-day CSVs the scheduled tasks read
        └──► build_workbook.py ──► the analysis spreadsheet
```

Everything downstream of `classify.py` is deterministic. Same inputs, same messages, every time.
That matters: Eric has already sent some of these, and a rebuild must not silently reword a message
that is already in someone's inbox.

### The first thing to know: nothing real is in this repo

Every file you will find here is code, synthetic data, or company research from public sources. The
people, the client roster and the drafted messages are not. They live in `data/`, which `.gitignore`
excludes in full, and the repo is built so that a clone with an empty `data/` still runs:

| Runtime file | Where it comes from | What happens if it is missing |
|---|---|---|
| `data/work/account_map.json` | extracted from the CRM export | falls back to `data/sample/account_map.sample.json`, which is invented |
| `data/work/storm_openers.py` | written each morning by the desk job | falls back to the empty template in `pipeline/`, and the storm tab is just absent |
| `data/work/plan_change_log*.csv` | written by the selection scripts | only the workbook's Changes tab needs them |
| `data/work/plan_with_copy_final.csv` | `make plan` | `make sample` invents 60 people in the same schema |

So `make setup && make sample && make check && make serve` gives you the whole front end, running,
with nobody's data on your machine. Do your development against that. Ask Eric for real data only
when you need to reproduce something specific, and put it outside the working tree with
`HUSTAD_DATA=/some/secure/path` when you do.

The zip this repo arrived in has a `PRIVATE_DO_NOT_COMMIT/` folder beside it holding the three
runtime files above. They go in `data/work/`. They do not go in git, and the `.gitignore` is written
so that they cannot go in git by accident.

## 2. The pieces worth understanding

### copy_engine.py

The interesting file. It composes every message from banks of fragments rather than generating
prose, because a cold DM that reads like software gets deleted before its argument is heard.

Each message follows the Sales Brain arc, compressed to four blocks:

```
Hi {First},

{their reality: a verified company fact, or a role truth, or the budget season question}

{evidence translated into what that role actually deals with}

{the give from their role stack, and one small ask with the exit open}
```

**The first ask is always the give, never a meeting.** A sample report, a checklist, a one-pager.
The meeting ask lives in touch three. This is from the Buyer Psychology Playbook and it is the
single biggest driver of reply rate on cold traffic.

Selection is deterministic per person (`md5(url_key)`) and constrained by three dedup layers:

| Layer | Rule | Why |
|---|---|---|
| Day | no two messages that day share an opener, middle, or closing ask | Eric reads them in a row and spots a template instantly |
| Firm | no two people at one firm ever share an opener, on any day | colleagues compare DMs |
| Plan | no fragment used more than 8 times overall | keeps the corpus from collapsing onto its favourites |

**Firm uniqueness outranks day uniqueness.** When a bank runs dry the code repeats within a day
before it repeats within a firm, because a stranger cannot see the duplication and a colleague can.

`qa()` is the linter. It fails a message for: over 90 words, more than one question or none, an em
or en dash, an exclamation mark, fewer than three paragraph blocks, missing blank lines, no
contraction anywhere (which is what stiff reads like), banned corporate vocabulary, phrases that
were overused in earlier versions, and any language implying ground-up construction. It takes the
company name so that a firm called "Elevate Property Partners" does not trip the ban on "elevate".

### build_desk.py

Builds the one page Eric uses. It is a self-contained HTML document with the send queue embedded as
JSON and no external dependencies except Google Fonts.

Two things about it are non-obvious:

**The send log lives in the browser.** `localStorage`, keyed to the page's origin. It survives
republishing to the same URL, which is what lets a scheduled task rebuild the page every morning
without destroying Eric's ticks. Nothing server-side holds it. `--from-log` reseeds from an
exported CSV as a backstop.

**The page can republish itself.** Inside the Claude artifact host it carries a base64 copy of its
own template and calls `claude.use('artifact').publish()` to save the log across devices. There is
an assertion in the build that the quine round-trips. Outside that host the call resolves null and
the page falls back to localStorage silently. Same for the CSV download: host capability when
present, plain Blob otherwise, one button either way.

`--standalone` emits a full HTML document for a web server. Without it you get a fragment, because
the Claude artifact host supplies its own document skeleton.

### storm_openers.py

`pipeline/storm_openers.py` is an empty template that documents the shape. The real one is
`data/work/storm_openers.py`, rewritten every morning by a scheduled job; `build_desk.py` loads
whichever it finds, live first. It is a python module rather than JSON only because the messages are
multi-paragraph and a triple-quoted string is easier for a human to eyeball than escaped newlines.
If you move this to a database, keep something human-readable in the loop, because the daily
verification step is a person reading these before they go out. Holds that day's verified severe weather events and the
alternate openers written off them. Hustad does storm response, so a confirmed hail event in an
operator's market beats any stored hook, but only for a few days, which is why this never enters
the monthly plan.

Every event carries a date, a specific submarket, a measured severity and a source URL or it does
not ship. The most common failure mode here is a search result from a prior year that reads as
current; the job is explicitly told to confirm the year on every event.

### content_engine.py and studio.py

The content side works differently from the DM side, on purpose. DMs are 1,400 personalized
messages, so `copy_engine.py` is a generation system with dedup machinery. Posts are four a week
in Eric's public voice, so `content_engine.py` is hand written editorial held to a QA gate. The
gate has two layers. `voice_lint()` is `docs/CONTENT_STANDARDS.md` Part 1 made executable: the
"X is not Y. It is Z." construction, signpost and crutch phrases, symmetrical triplet closes,
hyphens, dashes and exclamation points all fail the build, on post text and on every word of
graphic and slide copy. `validate()` adds the consistency mechanics: no two text-only posting days
back to back, no stacked question closes, and at most about half of posts closing on a question.
On top sit the claim rules: the Roadmap's banned phrases, no new construction, hook length against
the fold, word caps, links out of the body, and any cost or lifespan figure must cite a source
from the FACTS table or the build fails. Read the standards doc before writing the next batch; it
is the bar Eric enforces hardest, and the linter only catches the mechanical half of it. The
calendar is code;
`data/work/content_calendar.json` is just its build product, which is why CI can validate it with
no data present.

`studio.py` renders the three content tabs and the designed assets. The SVG templates (stat card,
checklist card, carousel slides) deliberately use a system font stack because the PNG export path
serializes SVG into a canvas, where webfonts do not travel. All five brand colors sit in one BRAND
dict at the top of the file; swap them to the official brand guide values and every asset follows.

Two export paths produce identical files: a human clicks Download PNG or Print slides on the page,
or CI runs `worker/render_assets.py`. Keep them identical; the day they drift, the hand posted
weeks stop matching the automated ones.

### worker/post_scheduler.py

The only code that talks to LinkedIn. Text posts fully automated. Graphic and carousel posts
automated when the rendered asset exists. Company posts skipped with a plain log message until the
Community Management approval lands. DMs never, structurally: it consumes the content calendar,
which cannot contain one. Idempotent through `worker/state/posted.json`, which the workflow
commits back. `DRY_RUN=1` is the default; nothing goes live until the repository variable flips.

### paths.py and the two layouts

Everything imports `pipeline/paths.py` rather than hardcoding a path, and it resolves two different
layouts. In the repo, code is in `pipeline/` and data is in `data/`. In the OneDrive folder the
scheduled jobs work out of, every script and every CSV sits in one flat directory with no repo
around it. `paths.py` detects which one it is in and every other script runs unchanged in both.

That is why `make folder` copies `paths.py` and the full plan into the bundle: the folder is meant
to be self-sufficient, so a scheduled session can download it and run
`python3 build_desk.py --day 2026-09-14` with no setup at all. If you change a path, test both
layouts. Unzipping the bundle into an empty directory and running that command is the whole test.

## How to know you have not broken anything

Two levels, and the second one matters more than it sounds.

`make check` runs `scripts/check_invariants.py`: ten assertions covering message QA, the
no-new-construction rule, paragraph structure, one question per message, firm opener uniqueness,
send-day legality and firm caps. It exits non-zero on failure, so it belongs in CI. Run it against
synthetic data (`make sample && make check`) and it still catches most structural regressions.

The stronger test is **copy determinism**. Message selection keys off `md5(url_key)`, so
regenerating the copy must reproduce the previous file byte for byte. Keep a reference copy of
`plan_with_copy_final.csv` before you change anything in `copy_engine.py` or `hooks.py`, rerun
`make copy`, and diff the `touch1_dm`, `touch2_dm` and `touch3_dm` columns. Zero differences means
your change was safe. A non-zero count is not automatically wrong, but every changed row is a
message that may already be in somebody's inbox, so you have to look at the list and confirm none
of them has a send date in the past. That check caught the one real bug in this refactor: firm-level
opener dedup keyed off the exact company string, so "Homes of America" and "Homes of America LLC"
were treated as two firms and two colleagues got the same opening line. Five messages changed when
it was fixed, all of them scheduled three weeks out.

## 3. What runs on a schedule

Four Claude scheduled tasks, defined outside this repo. `docs/SCHEDULED_TASKS.md` has the detail.

| Job | When | What |
|---|---|---|
| Outreach Desk | weekdays 10:00 CT | researches the day's companies, writes storm openers, rebuilds the page |
| Reply Desk | weekdays 8:30, 10:30, 13:30, 16:30 CT | classifies inbound replies, drafts answers |
| Friday Review | Fridays 12:10 CT | the five numbers, opener comparison, copy critique |
| Monthly Refresh | 1st, 6:00 CT | new export, re-tier, top the plan back up, rebuild |

The Outreach Desk is the one that matters most, and the one most worth replacing with something you
control. At 40 a day only about 12 percent of target companies have a hand-researched hook, so the
plan ships a safe generic opener and the desk upgrades as many as it can each morning with live
research. That split is what lets volume and personalisation coexist.

## 4. What is deliberately unfinished

I built for Eric working alone on one machine during one hour a day. Every shortcut below is a real
constraint, not an oversight, and each is the natural thing to fix first.

**The log has no server.** localStorage means one browser. Clear site data and it is gone; the
weekly CSV export to OneDrive is the only backup. It is also why the Friday review reads a file Eric
has to remember to download.

**There is no auth.** The page assumes the only person who can reach it is Eric. That is true of a
private Claude artifact and false of anything you deploy.

**Reply state is manual.** Eric ticks "Replied" and the page halts that person's later touches
locally. Nothing watches the inbox and updates the plan; the Reply Desk drafts answers but does not
write back.

**The OneDrive folder is a hand-carried handoff.** The Microsoft Graph connector can read but not
write, because `Files.ReadWrite.All` was never admin-consented in the tenant. So a refresh produces
files that Eric drags into the folder manually. If IT grants that scope, a lot of manual steps go
away at once.

**The page carries the whole window inline.** Fifteen send days of messages, about 2.4 MB. Fine
today, wrong past a few hundred targets a day.

## 5. What I would build, in order

**1. Auth, before anything else.** This tool shows real people's names, employers and profile URLs.
Whatever the deploy target, put an identity check in front of it. Cloudflare Access or a
Netlify/Vercel password is an afternoon; do not skip it because the URL is unguessable.

**2. Move the log to a real store.** A single table gets you everything the current design cannot:

```sql
create table send_log (
  id          bigserial primary key,
  target_id   text        not null,
  touch       smallint    not null,
  send_date   date        not null,
  status      text        not null,       -- sent | skipped | replied
  sent_at     timestamptz,
  opener      text,                       -- standard | shared history | storm trigger
  past_employer text,
  note        text,
  updated_at  timestamptz not null default now(),
  unique (target_id, touch)
);
```

Keep localStorage as the offline write path and sync on reconnect; Eric's hour should not depend on
the network. Once this exists the Friday review reads the database instead of a file someone has to
remember to export, and the desk knows what is already sent without being told.

**3. Server-side daily build.** Move the page build to a cron job in your own infrastructure. The
research and storm scan can stay with Claude, which is the part that genuinely wants a model, but have it POST
findings to an endpoint rather than rebuilding the page itself. Then the page becomes a thin client
over the database and stops being a 2.4 MB document.

**4. Reply ingestion.** LinkedIn notification mail lands in Outlook and Graph can read it. Parse
sender and body, match to a target, write a reply row, halt the sequence automatically. This is the
highest-value automation left, because a follow-up sent to someone who already replied is the one
mistake that actually costs a relationship.

**5. Metrics.** Reply rate by lane, by segment, by opener type. The three-opener comparison
(planned / shared history / storm trigger) is the experiment that tells you whether the daily
research job is worth running at all. Right now it is computed weekly by reading a CSV.

## 6. Rules that must not be relaxed

The content system added one to the original four: any post carrying a cost or lifespan figure
must cite a FACTS entry with its source, and the roadmap's banned claim list is enforced in
`qa_post`. Marketing pressure to round a number up or drop a caveat fails the build. That is the
point.

These are in the code and in `scripts/check_invariants.py`. Two of them are commercial and two are
legal or ethical, and none of them are style opinions.

**Nothing may act on LinkedIn.** No bots, no scraping, no browser automation, no auto-messaging,
including anything that "just" opens the compose box. The official data export is the only ingestion
path. This is LinkedIn's terms and it is also the program's own governance. If a feature request
requires touching the platform programmatically, the answer is no and the alternative is to make the
paste faster.

**Hustad does not do new construction.** Only buildings that already stand. The linter enforces the
vocabulary; the target selection excludes purely-development roles. A message that offers ground-up
work is not just off-strategy, it tells a buyer we do not know our own business. This rule exists
because a message went out framed that way once and Eric caught it.

**No invented facts, ever.** Every company claim traces to `data/research/companies_research.json`
which carries source URLs. Every storm event needs a date, a submarket, a measured severity and a
link. When something cannot be verified, the correct output is the generic opener, not a plausible
guess. A false claim in a cold DM is worse than a boring one.

**No pricing, warranty promises, claim outcomes or deductible advice** in any drafted message. These
are trust-boundary items in the Sales Brain and they belong in a conversation with a human, not in
outreach copy.

## 7. Where the rest of the thinking lives

- `docs/ARCHITECTURE.md`: data model, file formats, how the pieces connect
- `docs/PRIVACY.md`: what data exists, where it may go, what to do if it leaks
- `docs/DEPLOY.md`: hosting options ranked by whether they keep PII private
- `docs/COPY_STANDARD.md`: the rules every message passes and why each exists
- `docs/CONTENT_STANDARDS.md`: Eric's house voice and compliance guide, enforced in `voice_lint()`
- `docs/VOICE_TELLS.md`: the running log of what slips past the linter, with the fix for each
- `docs/SERVICE_DELIVERY.md`: how a ticket actually flows, read this before writing service copy
- `docs/CADENCE.md`: the caps, the Friday rule and how to retire it, the threading trigger, the
  reply rate tripwire, and why time zone send ordering was rejected
- `docs/REPLY_ENGINE.md`: 22 reply categories, decision styles, buyer states, objections
- `docs/SCHEDULED_TASKS.md`: what the four jobs do and how they degrade
- `docs/PROGRAM_STATUS.md`: a pointer. The status doc itself names people, so it lives in
  `data/work/` and in the Claude project, not in git.

Two source documents govern the messaging and are not in this repo: the Hustad Sales Brain Operating
System v8 and the Buyer Psychology and Messaging Playbook v1.0. Ask Eric for them before changing
copy; `docs/COPY_STANDARD.md` is the compressed version.

Anything unclear, the fastest read is `pipeline/copy_engine.py` top to bottom. The docstring explains
the intent and the banks show the voice better than any description of it.
