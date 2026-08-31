# Engineering review

A hostile pass over the whole package before handoff: front end, pipeline, worker, deployment.
Everything found is listed, including what was accepted rather than fixed, so the next reviewer
does not re-litigate settled tradeoffs.

## Fixed in this pass

**The reply filter hid its own input.** Typing in the Reply Center filter hid every panel,
including the one containing the search box, so one keystroke made the input disappear. The intro
panel is now marked `data-keep` and excluded from filtering.

**Copy buttons were wired twice.** The per-card wiring and the per-draft wiring both attached to
the first Copy button in a card, so one click wrote the clipboard twice and the label flickered.
Wiring is now once per draft block, and each button copies exactly its own block's payload, which
also fixes R3's second template (the message to the referred person) copying the wrong text.

**Header controls flashed on load.** The day navigation and progress bar are Outreach-only and
were hidden by a `:not()` rule until JS ran, which on the artifact host (where the page is a
fragment and scripts run late) meant a visible flash with no controls. Inverted: the default state
shows them, and JS adds `tab-other` when leaving the Outreach tab.

**The worker crashed raw on API errors.** An expired token produced a traceback instead of the
promised instruction. HTTP errors now map to messages that say what to do: 401 explains the 60 day
token life and which secret to rotate; 429 says why a rate limit at four posts a week means a loop
and points at the state file. Media upload failures name the file.

**CI rendered assets at half the resolution of the page.** `render_assets.py` produced 1200 px
PNGs while the page's Download PNG produces 2x. CI now renders at `device_scale_factor=2`, so an
automated Wednesday and a manual Wednesday ship the same file.

**The posting workflow could lose the state commit.** A human push between checkout and the
worker's `git push` would fail the workflow after a successful publish, which is the worst order:
posted on LinkedIn, not recorded. The workflow now rebases before pushing.

**`make site` could build from a stale calendar.** Page builds now regenerate and validate the
calendar first (`site` and `desk` depend on `content`), so an edit to `content_engine.py` cannot
ship half-applied.

**Tab semantics.** The tab rail now carries `role="tablist"` / `role="tab"` / `aria-selected`,
and selection is keyboard reachable since the tabs are real buttons.

**Dead code** in `render_posts_pane` (a leftover grouping loop) removed.

## Accepted, with reasons

**Page weight, 2.9 MB.** The self-save design requires the page to carry its own template as
base64, which roughly doubles content weight. At 16 send days and 32 calendar posts that is 2.9 MB
served, ~600 KB over the wire on any host with gzip (both the artifact host and any sane static
host compress). Acceptable for a desktop work tool; the lever if it ever matters is `--days 10`,
which drops the window, not the features. Revisit only past a few hundred targets a day, which is
the same threshold at which the whole inline-page design retires (NOTES section 4).

**The global `@page` size.** Printing the whole page normally inherits the carousel's 4:5 page
size. Nobody prints this page for any reason except the carousel flow; scoping `@page` per-print
is not worth the machinery.

**Assets are dark-ground regardless of theme.** The outbound cards are brand assets, not UI, so
they do not follow the viewer's light/dark theme. Deliberate.

**`urllib` over `requests`.** The worker has zero runtime dependencies on purpose: it must run in
a bare Actions container, a laptop, or the OneDrive flat folder without a pip step. Three calls a
post does not need a session pool.

## For Aminul's backlog, in order of real risk

1. **Token expiry is the operational failure mode.** Sixty days after go-live the worker will 401
   on a Tuesday morning. The workflow surfaces it loudly, but add the preflight: a Monday job that
   calls `/v2/userinfo` and opens an issue when the token has under seven days left.
2. **The send and content logs still live in one browser.** The Postgres schema in NOTES section 5
   now needs a `content_log` twin of `send_log`. Same shape, same reasoning.
3. **Analytics are hand-logged.** After Community Management approval, pull organization post
   impressions into the Friday review; member post analytics have no API, so personal post results
   stay manual (comment counts are visible; log them Fridays).
4. **The artifact and the deployed page will coexist for a while.** They share nothing but the
   build. Retire the artifact only after the deployed page has auth and Eric has moved his
   bookmark; localStorage does not migrate between origins, so the desk's `--from-log` reseed path
   is the migration tool (export send_log.csv from the old page, rebuild with `--from-log`).


## Addendum: renderer and linter changes for the Content Standards (August 27, evening)

The asset renderers now load Lora and Poppins from Google Fonts and wait on `document.fonts.ready`
before capturing, so CI PNGs and carousel PDFs carry the house faces; offline they fall back to
Georgia and Helvetica rather than failing the run. The in-page Download PNG remains a system-font
quick export and says so on its hint; the in-page carousel print inherits the page's webfonts and
is final quality. A `photo` post format was added for the Saturday real-photo slot: the worker
skips it by design (a human chooses and clears the photo), and the desk card carries the
compliance checklist. The voice linter runs inside `make check`, so a cadence violation anywhere
in the calendar breaks the build the same way a QA failure in the DM copy does.
