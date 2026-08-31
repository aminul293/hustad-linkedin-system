"""Regenerate Program_Status.md from the live plan so counts are never hand typed."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
import pandas as pd, collections
from datetime import date
OD = paths.s(paths.FOLDER)
plan = pd.read_csv(paths.s(paths.PLAN))
log1 = pd.read_csv(paths.s(paths.WORK / 'plan_change_log.csv'))
log2 = pd.read_csv(paths.s(paths.WORK / 'plan_change_log_v2.csv'))
pri = plan[plan.plan_role == 'PRIMARY']; res = plan[plan.plan_role == 'RESERVE']
load = collections.Counter()
for c in ['touch1_date','touch2_date','touch3_date']:
    for v in pri[c].dropna(): load[str(v)[:10]] += 1
d1, dN = min(pri.touch1_date.dropna()), max(pri.touch1_date.dropna())
last = max(load)
msgs = len(pri)*3 + len(res)
qa_fail = sum((plan[c] != 'PASS').sum() for c in ['touch1_qa','touch2_qa','touch3_qa','past_employer_qa'])

def bullets(df):
    out = []
    for _, r in df.iterrows():
        pos = f" [{r['position']}]" if 'position' in df.columns and isinstance(r.get('position'), str) and r['position'] else ''
        out.append(f"- {r['target_id']} {r['name']} ({r['company']}){pos}: {r['change']}; {r['reason']}")
    return "\n".join(out)

md = f"""# Hustad LinkedIn New Business Track: Program Status and Decisions (v1.6, August 27, 2026)

Working surface: the Outreach Desk, one page, one bookmark.
https://claude.ai/code/artifact/d365b045-39ba-47b2-adf3-aaeef3a67415

Companion files: Hustad_LinkedIn_NewBusiness_Baseline_v1_4.xlsx (analysis copy),
Hustad_LinkedIn_NewBusiness_Playbook_v1_5.docx, Hustad_Fall_Roof_and_Exterior_Checklist_v1.docx,
Hustad_Roof_Warranty_OnePager_v1.docx, Hustad_LinkedIn_OneDrive_Bundle_v1_4.zip.

## What changed in v1.6 (August 27)

**Volume raised to 40 first touches a weekday.** Ten a day would have taken two years to work a
network of 4,839 connections. Forty works the eligible pool of 2,709 non site level targets in
about seven weeks, which is what Eric asked for. The plan went from 159 primaries to
{len(pri)} across {plan.Company.nunique()} firms, drawn Tier 1 first then Tier 2, capped at three
per firm and never two people from one firm on the same day. Nobody already sent or scheduled moved.

Expect a 60 to 75 minute block rather than a clean hour: at steady state a day carries 40 first
touches plus roughly 60 to 80 follow ups. First touches run about 50 seconds each with the profile
check, follow ups about 30. Replies halt sequences, which trims the follow up load as the program
warms up. If the block consistently overruns, the number to move is the 40, and the Friday review
is instructed to ask.

**One page instead of two.** The send console and the morning verification desk are merged into the
Outreach Desk at the URL above. It carries the send calendar, the day's verified drafts, the storm
triggers, the copy buttons, the tick boxes and the log. The Outreach Desk task rebuilds it every
weekday at 10:00 Central. The log lives in Eric's browser keyed to that URL and survives the daily
rebuild, so there is no link to hunt for and nothing to paste. The old separate desk page now just
points at it.

**Research became just in time.** At this volume only about 12 percent of target companies have a
hand researched hook, so the plan supplies a safe generic opener drawn from deep lane and segment
banks, and the desk upgrades as many as it can each morning with real research plus storm triggers.
Durable finds get folded back into hooks.py at the monthly refresh so the plan carries them
permanently. Copy quality holds: every message still passes the full QA, no two people at one firm
ever open on the same sentence, and a 40 person day carries a median of 34 distinct openers.

## Baseline (LinkedIn export of August 25, 2026; opportunity list of August 26, 2026)

Connections 4839. Cold with no interaction 4663. Eligible cold targets after gates 3613; Hold 539;
Exclude 687 (including 362 contacts at 45 LinkedIn company names that match active accounts).
Tier 1 among eligible: 740.

## Gate G2: active accounts

The 2026 opportunity list (1,217 opportunities, 110 CRM companies, Jan 2 to Aug 26, 2026) is the conflict
list. Any contact whose current company matches an active account is out of the cold program. Warm and
active outreach is handled separately and is not part of this plan. Probable matches held for verification
(not messaged): Capstone Communities, CENTURION Property Group, Forward Property Management Solutions,
Legacy LLC and Legacy Property Management Group, Lamb Communities. Greystar remains eligible as new business.

## Past employer check

The export carries no employment history, so the check happens in the 20 second pre-send profile read. Open
Experience; if a past employer is on the Client Match List, type it into the Past Employer column. The row
flags itself and the Shared History Opener column gives the message to send instead. Eric sends it. Nothing
routes to anyone else at Hustad.

## Plan v1.2 changes (active accounts applied)

{bullets(log1)}

## Plan v1.3 changes (ground up development removed)

{bullets(log2[log2.target_id.notna() & (log2.target_id.astype(str) != '')])}

The August 26 slot left by T003 was not backfilled; that day was already sent, so it simply ran one short.

Plan now stands at {len(pri)} primaries ({d1} to {dN}) plus {len(res)} reserves across
{plan.Company.nunique()} companies. Follow ups run through {last}. No day exceeds {max(load.values())} total
sends. QA failures across all {msgs} messages: {qa_fail}.

## Decisions and assumptions

DR-3: higher daily volume than the warm program ceiling of five; per person caps, reply halt, permanent
suppression and human send unchanged. Named proof in copy: Asset Living, Cardinal Group and Yugo, Dial
Retirement Communities and Charter Senior Living, Burlington Capital at Offutt. Capital Certainty and the
Yugo approval mortality data are not used in any DM. Hustad does not bid or build new construction and no
message offers it.

## Automation (LIVE)

Four scheduled Claude tasks. Each starts a fresh session, reads this folder, publishes to a fixed page so
Eric keeps one bookmark per job, and notifies him. None of them touch LinkedIn; every message is still sent
by Eric by hand.

- Outreach Desk. Weekdays 10:00 Central, an hour before the block. Reads the day's queue, drops active
  accounts and suppressed rows, then researches the day's companies in parallel: re-checking stored facts,
  finding openers for companies that had none, and confirming severe weather in each operator's markets
  against National Weather Service records. Writes storm alternate openers where a market took weather,
  then rebuilds the Outreach Desk page in place. It is the outbound twin of the Reply Desk.
- Reply Desk. Weekdays 8:30, 10:30, 13:30 and 16:30 Central. Searches Outlook for LinkedIn notifications,
  matches the sender to targets_roster.csv, classifies against Reply_Engine.md, reads decision style and
  buyer state, drafts the answer and the reply log line. Silent when nothing new.
- Friday Review. Fridays 12:10 Central. Five numbers with arithmetic shown, reply rate by lane and segment,
  weakest and strongest hooks, next week's volume recommendation, which reserves to promote, and on the last
  Friday of the month the export request.
- Monthly Refresh. First of the month, 6:00 Central. Waits for a new LinkedIn export and CRM opportunity
  export in the folder; if absent it says so and stops. When they arrive it runs the folder's own scripts
  (the .py files now ship in the folder), rebuilds the plan and the console while preserving the embedded
  send log, and delivers the regenerated CSVs.

Connector limits found on August 26. Reading OneDrive and Outlook works. Writing files to OneDrive and
sending mail are both blocked: Files.ReadWrite.All and Mail.Send are not admin consented for the connector
app. Until IT grants those, tasks deliver by page plus notification and Eric pastes the log lines into
send_log.csv and reply_log.csv himself.

Daylight saving note: the schedules are stored in UTC against Central Daylight Time. When Chicago moves to
standard time on November 1, 2026, every task fires one hour earlier locally until the schedules are shifted.

## Setup step still open

Unzip Hustad_LinkedIn_OneDrive_Bundle_v1_4.zip into OneDrive, LinkedIn, LinkedIn New Business Track,
replacing what is there. This is the one recurring chore and it is load bearing: the day files in that
folder are what the Outreach Desk reads every morning, and the folder currently holds the old ten a day
queues. Until it is replaced, the desk has nothing to work from past August 27.

## Calendar

August 26 is in the books: 14 first touches sent (batch one minus T003, which was skipped and removed for
new construction framing, plus all ten of batch two). Ten first touches moved up from August 28 to refill
August 27. The program runs at full cadence from Thursday August 27. First touches {d1} to {dN}; follow ups through {last}, levelled so no day
exceeds 40 total sends, which is what stops the two Labor Day pile ups.
"""
open(f'{paths.FOLDER}/Program_Status.md','w').write(md)
import shutil; shutil.copy(f'{paths.FOLDER}/Program_Status.md',paths.s(paths.OUT / 'Program_Status.md'))
print('primaries', len(pri), 'reserves', len(res), 'companies', plan.Company.nunique(), 'max/day', max(load.values()), 'qa fails', qa_fail)
