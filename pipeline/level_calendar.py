"""
Keep the send calendar inside its caps by pushing work forward, never backward.

Two caps, and they mean different things:

  DAY_CAP        total sends on any one day, first touches plus follow ups.
  FRIDAY_FIRST   first touches allowed on a Friday.

The Friday cap exists because cold outreach lands worst at the end of the week. The
directional figure behind it is roughly 35 percent below the weekly average on Friday
against a Tuesday to Thursday peak, from Growleads campaign data covering 400 plus
campaigns in 2025 and 2026. That is cold email rather than LinkedIn DM, and it is one
vendor's own campaigns, so it is a reason to cap rather than a law. The Friday Review
reports reply rate by send day from Hustad's own log, and after six weeks that number
either confirms the cap or retires it. Set FRIDAY_FIRST to 40 to turn it off.

Follow ups are never subject to the Friday cap. They sit inside threads that already
exist, and moving them would break the spacing promise the sequence is built on.

Nothing dated before START moves, ever. Some of those messages are already sent.
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
import pandas as pd, collections
from datetime import date, timedelta

DAY_CAP = 120           # total sends in a day
FIRST_CAP = 40          # first touches on a normal day
FRIDAY_FIRST = 15       # first touches on a Friday
START = date(2026, 8, 28)
HOLIDAYS = {date(2026, 9, 7), date(2026, 11, 26), date(2026, 11, 27),
            date(2026, 12, 24), date(2026, 12, 25), date(2027, 1, 1)}
P = paths.s(paths.PLAN)

def nb(d):
    """Next business day that is not a holiday."""
    while d.weekday() > 4 or d in HOLIDAYS:
        d += timedelta(days=1)
    return d

def first_cap(d):
    return FRIDAY_FIRST if date.fromisoformat(d).weekday() == 4 else FIRST_CAP

p = pd.read_csv(P)
pr = p.plan_role == 'PRIMARY'

load = collections.Counter()      # all sends per day
firsts = collections.Counter()    # first touches per day
for c in ['touch1_date', 'touch2_date', 'touch3_date']:
    for v in p.loc[pr, c].dropna():
        load[str(v)[:10]] += 1
for v in p.loc[pr, 'touch1_date'].dropna():
    firsts[str(v)[:10]] += 1

moved = []

# ---------------------------------------------------------------------------
# 1. Re-deal first touches from START forward under both caps.
#
#    A naive "push the overflow to the next day with room" fills every day to 40 and
#    dumps the deferred rows at the very back of the plan, which puts Tier 1 targets
#    behind Tier 2. So instead: take every unsent first touch, keep them in their
#    current priority order (date, then day_seq, which is how the plan encodes tier),
#    and deal them back into days in that order under the caps. Relative priority is
#    preserved exactly and the tail grows by the minimum amount arithmetic allows.
#
#    A row's follow ups move with it by the same shift, so the 7 and 14 day spacing
#    survives. The one firm one day rule is carried through the deal.
# ---------------------------------------------------------------------------
movable = [i for i in p.index[pr & p.touch1_date.notna()]
           if str(p.at[i, 'touch1_date'])[:10] >= START.isoformat()]
movable.sort(key=lambda i: (str(p.at[i, 'touch1_date'])[:10],
                            float(p.at[i, 'day_seq']) if pd.notna(p.at[i, 'day_seq']) else 99.0))

def fam(c):
    return ' '.join(str(c).lower().replace(',', ' ').split()[:2])

# clear the movable rows out of the counters; frozen history stays counted
for i in movable:
    for c in ['touch1_date', 'touch2_date', 'touch3_date']:
        v = p.at[i, c]
        if isinstance(v, str) and v:
            load[str(v)[:10]] -= 1
    firsts[str(p.at[i, 'touch1_date'])[:10]] -= 1

day_firms = collections.defaultdict(set)
for i in p.index[pr & p.touch1_date.notna()]:
    d = str(p.at[i, 'touch1_date'])[:10]
    if d < START.isoformat():
        day_firms[d].add(fam(p.at[i, 'Company']))

cur = nb(START)
for i in movable:
    old_d = date.fromisoformat(str(p.at[i, 'touch1_date'])[:10])
    firm = fam(p.at[i, 'Company'])
    d = max(cur, nb(START))
    while (firsts[d.isoformat()] >= first_cap(d.isoformat())
           or load[d.isoformat()] >= DAY_CAP
           or firm in day_firms[d.isoformat()]):
        d = nb(d + timedelta(days=1))
    shift = (d - old_d).days
    firsts[d.isoformat()] += 1
    day_firms[d.isoformat()].add(firm)
    for c in ['touch1_date', 'touch2_date', 'touch3_date']:
        v = p.at[i, c]
        if isinstance(v, str) and v:
            nvd = nb(date.fromisoformat(str(v)[:10]) + timedelta(days=shift)).isoformat()
            load[nvd] += 1
            if nvd != str(v)[:10]:
                p.at[i, c] = nvd
    if shift:
        moved.append((p.at[i, 'target_id'], 'first touch', old_d.isoformat(), d.isoformat()))
    # advance the cursor only when a day fills, so the deal stays dense
    while firsts[cur.isoformat()] >= first_cap(cur.isoformat()) or load[cur.isoformat()] >= DAY_CAP:
        cur = nb(cur + timedelta(days=1))

# ---------------------------------------------------------------------------
# 2. Follow ups over the total day cap move forward one business day at a time.
# ---------------------------------------------------------------------------
for col in ['touch2_date', 'touch3_date']:
    idx = p.index[pr & p[col].notna()].tolist()
    idx.sort(key=lambda i: str(p.at[i, col]))
    for i in idx:
        d = str(p.at[i, col])[:10]
        if load[d] <= DAY_CAP or date.fromisoformat(d) < START:
            continue
        nd = nb(date.fromisoformat(d) + timedelta(days=1)).isoformat()
        load[d] -= 1; load[nd] += 1
        moved.append((p.at[i, 'target_id'], col, d, nd))
        p.at[i, col] = nd

p.to_csv(P, index=False)

over_first = [(k, v) for k, v in sorted(firsts.items())
              if v > first_cap(k) and date.fromisoformat(k) >= START]
over_day = [(k, v) for k, v in sorted(load.items()) if v > DAY_CAP]
last = max(firsts) if firsts else ''
print(f'moved {len(moved)}', moved[:5])
print(f'max sends/day {max(load.values()) if load else 0} (cap {DAY_CAP}) | over: {over_day}')
print(f'first touches over cap: {over_first or "none"} | last first touch {last}')
