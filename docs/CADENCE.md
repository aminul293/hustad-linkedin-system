# Cadence standard

What the calendar does and why. Copy rules, gates, tiers, cooldowns and trust boundaries are
elsewhere and unchanged; this covers volume, day shape and the rules that move dates.

## The caps

| Cap | Value | Where it lives |
|---|---|---|
| First touches, normal day | 40 | `level_calendar.FIRST_CAP` |
| First touches, Friday | 15 | `level_calendar.FRIDAY_FIRST` |
| Total sends any day | 120 | `level_calendar.DAY_CAP` |
| People per firm in the plan | 3, more only for the largest platforms | `scale_plan.py` |
| People from one firm on one day | 1, always | enforced in the deal and in `make check` |

Nothing dated before `level_calendar.START` ever moves. Some of it is already sent.

## The Friday cap, and how to retire it

Cold outreach lands worst at the end of the week. The number behind the cap is roughly 35 percent
below the weekly average on Friday, against a Tuesday to Thursday peak, from Growleads campaign
data across 400 plus campaigns in 2025 and 2026.

Read that source honestly: it is cold email rather than LinkedIn DM, and it is one vendor
reporting on its own campaigns. It justifies a cap, not a law. So the Friday Review reports reply
rate by send day of week from Hustad's own send log, and after about six weeks that number either
confirms the cap or retires it. Set `FRIDAY_FIRST = 40` to turn it off; nothing else changes.

The arithmetic cost: capping Fridays defers about 25 first touches each Friday into the rest of the
week under the same ceiling. The first touch tail runs to about October 26 rather than October 16.
Weekly throughput goes from 200 to 175.

## How deferred rows are chosen

Not by pushing the overflow to the next day with room. That fills every day to 40 and dumps the
deferred rows at the very back, which puts Tier 1 targets behind Tier 2.

Instead `level_calendar.py` re-deals: it takes every unsent first touch, holds them in their current
priority order (date, then `day_seq`, which is how the plan encodes tier), and deals them back into
days under the caps. Relative priority survives exactly, the days stay dense, and the tail grows by
the minimum the arithmetic allows. A row's follow ups shift with it, so the 7 and 14 day spacing is
preserved.

## The threading trigger

When anyone at a firm replies, the other targeted people there stop being cold. Somebody in that
building has heard of Hustad and the topic is live. `thread_firm.py` pulls those colleagues forward
to inside five business days.

The calendar is normally full, so the window is held by displacing rather than by giving up: the
lowest priority cold row on the best available day goes to the tail and the colleague takes the
slot. Daily count unchanged, better order.

Two rules carry through. Never two people from one firm on one day, because colleagues compare DMs.
And the colleague's reply is never mentioned in the message, unless that colleague was asked "who
else on your side should see this" and named the person. That is a conversation Eric has; no script
can infer it.

```
python3 pipeline/thread_firm.py --log send_log.csv            # dry run
python3 pipeline/thread_firm.py --log send_log.csv --apply
make folder                                                    # so the desk sees the new dates
```

## Reply rate, measured honestly

Count replies only against first touches at least three business days old. Fresh sends have not had
time to reply and including them makes a healthy week look like a failing one. The Friday Review
does this arithmetic and shows its work.

What to expect for this format, messages to existing first degree connections, give first, no
pitch: LinkedIn's platform wide message reply rate is 10.4 percent, from Expandi's H2 2026 report
covering 13.2 million connection requests and 6.7 million outbound messages sent through 13,302
accounts between May 2025 and April 2026. Treat 8 to 12 percent on Touch 1 as the working band and
the full three touch sequence as 15 to 20 percent cumulative.

Small numbers lie. At a true 10 percent reply rate, 18 sends produce zero replies about 15 percent
of the time by chance alone (0.9 to the 18th is 0.150). Zero replies from 18 is not yet a signal.

## The volume tripwire

Measured on aged first touches, at 100 or more of them:

| Aged reply rate | Next week |
|---|---|
| 15 percent or better | Hold at 40 a day |
| Under 15 percent | Drop to 25 a day |
| Under 8 percent | Drop to 15 a day and audit the copy before resuming |

The ceiling never rises above 40. If the block consistently overruns the hour, the 40 comes down;
the hour does not stretch.

Hard stops, earlier than the tripwire: zero replies after 50 aged first touches, or under 5 percent
after 100. Both mean stop and audit targeting and copy before sending more.

## Send order within a day

Work the page top to bottom. Ordering by the recipient's time zone was considered and rejected
twice over: `company_hq` is present for only about a fifth of the plan, so most rows carry no
location at all, and the block runs 11:05 to 12:05 Central, which is 12:05 to 1:05 Eastern and
9:05 to 10:05 Pacific. Eastern first would front load the lunch hour and leave the best window,
Pacific morning, for the end of the block. If time zone ordering is ever revisited, it should run
West to East for a Central late morning block, and it needs location data the export does not
currently carry.

## What has not changed

Touch 1 is a give and never a meeting ask. Touch 2 is a different give. Touch 3 is the meeting ask.
Any reply halts the sequence. The 90 word ceiling, one question, one CTA, the gates, the cooldowns,
the trust boundaries, hand sending every message, weekends off.
