# Hustad LinkedIn New Business Track: Scheduled Tasks (v4, August 27, 2026)

The four scheduled Claude tasks as they run now. This version replaces the original design, in
which the 10:45 task rebuilt a daily console page and Eric pasted log lines back by hand. The
send console is now ONE standing artifact page carrying the whole calendar, and the send log
saves into the page itself every time Eric ticks a row, so the tasks read the log straight off
the page and nothing about sends gets pasted anywhere.

Eric's one bookmark: https://claude.ai/code/artifact/d365b045-39ba-47b2-adf3-aaeef3a67415
The console and the morning desk are one page now. The log lives in his browser keyed to that URL
and survives the daily rebuild, so tasks rebuild the page freely and never need to read it back.
send_log.csv in OneDrive is the archive; he downloads it from the page about once a week and that
is what the Friday review reads.

## The four tasks

**1. LinkedIn Outreach Desk** (trigger trig_01EsFUf6HkwwqMTtutQgwVXp)
Weekdays 10:00 Central (cron 0 15 * * 1-5 UTC), an hour before the block.
Page: https://claude.ai/code/artifact/d365b045-39ba-47b2-adf3-aaeef3a67415

The outbound twin of the Reply Desk. Where the Reply Desk turns an incoming message into a
classified, drafted answer, this turns an outgoing message into a verified one. For every first
touch scheduled today it re-checks the stored company fact against live sources, scans three
weeks of company news, watches for leadership changes that move the contact or put someone above
them, and searches National Weather Service records for confirmed severe weather in that
operator's markets. Where a market actually took weather, it writes a storm-trigger alternate
first touch and puts both drafts behind a Planned / Storm trigger toggle. It publishes one card
per person showing what was checked, what changed, the sourced events with links, and the copy
with a Copy button.

It rebuilds THE page in place each morning with build_desk.py, so Eric has one bookmark and never
hunts for a link. Since the page became the five tab Command Center, the same rebuild refreshes the
Posts, Newsletter and Articles tabs from content_calendar.json in the folder; on posting days the
morning notification should name the day's post alongside the DM count. Rebuilding is safe: his send log lives in browser storage keyed to that URL and
survives republishing. At 40 a day only about 12 percent of target companies have a hand researched
hook, so the desk's other job is upgrading generic openers to researched ones; durable finds get
reported so the Monthly Refresh can fold them into hooks.py permanently.

Two rules it enforces that matter more than freshness: a groundbreaking or a topping out is a new
building getting its roof and is never used as an opener, and an event without a date, a
submarket, a measured severity and a source URL does not go on the page. On its first run it
rejected ACC's TCU topping out and Kairoi's LoHi groundbreaking on exactly that basis, and killed
two storm stories that search results made look current but were from prior years.

Push and email notification. Skips weekends and Labor Day with a one-line note.

**2. LinkedIn Reply Desk** (trigger trig_016jorcBoyrS12m66saTiwfD)
Weekdays 8:30, 10:30, 13:30 and 16:30 Central (cron 30 13,15,18,21 * * 1-5 UTC). Sweeps Outlook
for LinkedIn message notifications, matches senders to targets_roster.csv, classifies each reply
against Reply_Engine.md (R1 to R21), reads decision style and buyer state, and drafts the answer
in Eric's voice on the Sales Brain arc, 90 words max, one question. R21 (they used to work at a
current client) always stays with Eric, never an internal handoff. Publishes one card per reply
to the "Hustad Reply Desk" page with copy buttons that preserve paragraph breaks, plus reply-log
rows in BOTH tab-separated form (pastes into spreadsheet columns) and CSV. Reminds Eric to tick
Replied in the console so remaining touches halt. Silent when there is nothing new.

**3. LinkedIn Friday Review** (trigger trig_01DxDFNeZMHySZ4DggAXfCbe)
Fridays 12:10 Central (cron 10 17 * * 5 UTC). The send log comes FROM THE CONSOLE PAGE (state
block), merged with the OneDrive reply_log.csv and the archival send_log.csv (console wins on
conflict). Computes the five numbers with arithmetic shown (sent vs plan, reply rate vs 20
percent, positive rate vs 10 percent, meetings and referrals, compliance count which must be
zero), breaks replies down by lane and segment, compares the THREE opener types against each
other (planned, shared history, and the desk's storm triggers, which Eric marks by typing "storm"
in that row's note field), critiques five random sent messages against the Sales Brain arc,
recommends next week's volume and reserve promotions, and asks for the monthly export on the
last Friday of the month. Publishes to the "Hustad Weekly Review" page.

**4. LinkedIn Monthly Refresh** (trigger trig_014HgZwGTWfpkDo7Jdya1w8C)
First of the month, 6:00 Central (cron 0 11 1 * * UTC). Waits for a new LinkedIn export and CRM
opportunity export in the folder; if absent, says so and stops. When present it runs THE FOLDER'S
OWN SCRIPTS (the .py files now ship inside the LinkedIn folder: classify, hooks, copy_engine,
recalendar, level_calendar, build_console_v2 and calendar_ref.csv): diff on profile URL,
engagement state, Gate G2, scoring, pinned reselection, copy regeneration through copy_engine.py
only. It reads the console state FIRST, rebuilds the console with build_console_v2.py --state so
the log survives, republishes to the same console URL WITHOUT passing capabilities (the page's
stored declaration carries forward), publishes the "Hustad Monthly Refresh" report, and delivers
the new day CSVs for Eric to drop into the folder. Band A = Moves and Role changes at fitting
accounts, worked within 14 days; a move into a purely development role is a removal, not a lead.

## Rules carried by every task

Nothing acts on LinkedIn; Eric sends every message by hand. Hustad does not do new construction,
and any queued copy implying it is flagged as a bug, never sent. Past employment at a current
client is Eric's own shared-history opener. No invented contacts, facts or numbers; a missing
source is reported as missing. No pricing, warranty promises, claim outcomes or deductible
advice. No em or en dashes; ranges written "X to Y".

## The artifact-read constraint, and how each task degrades

Discovered August 27: this cloud environment's network allowlist blocks reads of published
artifacts (the error names frame.claudeusercontent.com). Every task that reads the console is
written to survive it rather than fail:

The architecture originally routed around this: every task read OneDrive CSVs and nothing read the
page. Then the page learned to save new versions of itself (every tick Eric makes publishes one),
and the platform rightly refuses any publish that was not built on the latest version. From that
moment the allowlist entry stopped being a nice to have:

**Allowing `*.frame.claudeusercontent.com` (environment settings, Code, Network access, Custom,
Allowed domains) is now required for the daily rebuild.** With it, the desk and refresh tasks read
the live page first, seed the rebuild from its embedded state (so Eric's ticks travel to his other
devices), and publish cleanly. Without it, the tasks cannot publish over Eric's own saves; they
degrade to delivering findings as plain messages, and the page simply stays as Eric last used it,
log intact. Both task prompts carry the read-first step and the degraded path explicitly.

- **Outreach Desk** reads the day's queue from OneDrive, reads the live page for state, rebuilds
  all five tabs, publishes to the same URL. Title "Hustad LinkedIn Desk", favicon unchanged.
- **Friday Review** reads send_log.csv and, when present, content_log.csv in OneDrive, freshness
  checked first so a stale archive is never reported as a slow week.
- **Monthly Refresh** rebuilds the page the same way the desk does, and revalidates the content
  calendar's runway.

The OneDrive folder carries three reference docs that any scheduled session writing in Eric's name
reads first: `CONTENT_STANDARDS.md`, the house voice and compliance guide, whose banned patterns are
also enforced mechanically in both copy engines' QA; `VOICE_TELLS.md`, the running log of the
patterns that slip past the linter; and `SERVICE_DELIVERY.md`, how a ticket actually flows from the
account manager or the portal through morning dispatch, closeout and reporting. That last one exists
because a draft once had a crew on a roof at two in the morning, which is not how roofing works.

## The chore that keeps it all running

The OneDrive folder is the handoff between this session and the daily tasks. The day files there
are what the desk reads every morning. When a refresh delivers new sendqueue files, they have to be
dropped into the folder, replacing what is there, or the desk runs out of queue. That is the one
recurring manual step and it is load bearing.

## Operational notes

The Microsoft 365 connector reads OneDrive and Outlook but cannot write files or send mail
(Files.ReadWrite.All and Mail.Send lack admin consent), which is why delivery is by artifact
page plus notification and why the monthly refresh hands files back through the session.
Schedules are stored in UTC against Central Daylight Time: when Chicago returns to standard time
on November 1, 2026, every task fires an hour earlier locally until the crons are shifted.
The Reply Desk depends on LinkedIn notification emails, which stop for messages Eric reads in
the LinkedIn app before a sweep; those can be pasted into the project for the same treatment.
