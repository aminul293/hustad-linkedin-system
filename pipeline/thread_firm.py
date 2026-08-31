#!/usr/bin/env python3
"""
The threading trigger.

When anyone at a firm replies, the other targeted people at that firm stop being cold.
Somebody there has now heard of Hustad, the topic is live in the building, and a message
that arrives three weeks later has lost the only advantage it had. This pulls those
colleagues forward to inside five business days.

Multithreading is the reason. A single contact at a large operator rarely owns the
exterior decision on their own; the regional, the asset manager and the facilities lead
each hold part of it. Reaching them while one of them is already engaged is worth more
than reaching them on the original schedule.

Two hard rules carried through from the plan:
  - Never two people from the same firm on the same day. Colleagues compare DMs.
  - The colleague's reply is never mentioned in the message. It is only ever referenced
    when that colleague was asked "who else on your side should see this" and named the
    person. That is a conversation Eric has, not something a script can infer.

Nothing here rewrites copy. It moves dates, and the desk picks the rows up tomorrow.

Usage:
    python3 thread_firm.py --log send_log.csv                 dry run, show what would move
    python3 thread_firm.py --log send_log.csv --apply         write the new dates
    python3 thread_firm.py --company "Greystar" --apply       thread one firm by hand
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
import pandas as pd, csv, collections
from datetime import date, timedelta

WINDOW = 5              # business days to reach the colleagues in
FIRST_CAP = 40
FRIDAY_FIRST = 15
DAY_CAP = 120
HOLIDAYS = {date(2026, 9, 7), date(2026, 11, 26), date(2026, 11, 27),
            date(2026, 12, 24), date(2026, 12, 25), date(2027, 1, 1)}

def arg(name, default=''):
    a = sys.argv[1:]
    return a[a.index(name) + 1] if name in a else default

def nb(d):
    while d.weekday() > 4 or d in HOLIDAYS:
        d += timedelta(days=1)
    return d

def first_cap(d):
    return FRIDAY_FIRST if date.fromisoformat(d).weekday() == 4 else FIRST_CAP

def fam(c):
    """Arlington Properties Inc and Arlington Properties LLC are colleagues, not two firms."""
    return ' '.join(str(c).lower().replace(',', ' ').split()[:2])

def replied_firms(log_path):
    """Firms with at least one reply, from the send log the desk exports."""
    firms = {}
    try:
        for r in csv.DictReader(open(log_path)):
            note = (r.get('Notes') or '').lower()
            status = (r.get('Status') or '').lower()
            if 'replied' in note or status == 'replied':
                firms.setdefault(fam(r.get('Company', '')), r.get('Company', ''))
    except FileNotFoundError:
        print(f'no send log at {log_path}')
    return firms

def main():
    apply = '--apply' in sys.argv
    p = pd.read_csv(paths.s(paths.PLAN))
    pri = p.plan_role == 'PRIMARY'
    today = date.fromisoformat(arg('--today') or date.today().isoformat())

    one = arg('--company')
    firms = {fam(one): one} if one else replied_firms(arg('--log', 'send_log.csv'))
    if not firms:
        print('no replies in the log yet, nothing to thread'); return 0

    load, firsts = collections.Counter(), collections.Counter()
    day_firms = collections.defaultdict(set)
    for i in p.index[pri]:
        for c in ('touch1_date', 'touch2_date', 'touch3_date'):
            v = p.at[i, c]
            if isinstance(v, str) and v:
                load[str(v)[:10]] += 1
        v = p.at[i, 'touch1_date']
        if isinstance(v, str) and v:
            firsts[str(v)[:10]] += 1
            day_firms[str(v)[:10]].add(fam(p.at[i, 'Company']))

    deadline = today
    for _ in range(WINDOW):
        deadline = nb(deadline + timedelta(days=1))

    moved = []
    for key, shown in sorted(firms.items()):
        rows = [i for i in p.index[pri & (p.Company.map(fam) == key)]
                if isinstance(p.at[i, 'touch1_date'], str)
                and str(p.at[i, 'touch1_date'])[:10] > today.isoformat()]
        for i in rows:
            old = str(p.at[i, 'touch1_date'])[:10]
            if date.fromisoformat(old) <= deadline:
                continue                      # already inside the window
            d = nb(today + timedelta(days=1))
            while (firsts[d.isoformat()] >= first_cap(d.isoformat())
                   or load[d.isoformat()] >= DAY_CAP
                   or key in day_firms[d.isoformat()]) and d <= deadline:
                d = nb(d + timedelta(days=1))
            # A saturated calendar is the normal case, so the window is held by displacing
            # rather than by giving up: the lowest priority cold row on the best available day
            # goes to the tail, and the colleague takes its slot. Same daily count, better order.
            if d > deadline:
                d, victim = None, None
                cand = nb(today + timedelta(days=1))
                while cand <= deadline:
                    if key not in day_firms[cand.isoformat()]:
                        same = [j for j in p.index[pri]
                                if isinstance(p.at[j, 'touch1_date'], str)
                                and str(p.at[j, 'touch1_date'])[:10] == cand.isoformat()
                                and fam(p.at[j, 'Company']) != key]
                        if same:
                            same.sort(key=lambda j: -(float(p.at[j, 'day_seq'])
                                                      if pd.notna(p.at[j, 'day_seq']) else 0.0))
                            d, victim = cand, same[0]
                            break
                    cand = nb(cand + timedelta(days=1))
                if victim is None:
                    moved.append((p.at[i, 'target_id'], shown, old, 'no room inside the window'))
                    continue
                # send the displaced row to the end of the first touch calendar
                tail = max(k for k in firsts if firsts[k])
                vd = nb(date.fromisoformat(tail))
                while firsts[vd.isoformat()] >= first_cap(vd.isoformat()) or \
                      fam(p.at[victim, 'Company']) in day_firms[vd.isoformat()]:
                    vd = nb(vd + timedelta(days=1))
                vshift = (vd - date.fromisoformat(str(p.at[victim, 'touch1_date'])[:10])).days
                firsts[d.isoformat()] -= 1; firsts[vd.isoformat()] += 1
                day_firms[vd.isoformat()].add(fam(p.at[victim, 'Company']))
                for c in ('touch1_date', 'touch2_date', 'touch3_date'):
                    v = p.at[victim, c]
                    if isinstance(v, str) and v:
                        nvd = nb(date.fromisoformat(str(v)[:10]) + timedelta(days=vshift)).isoformat()
                        load[str(v)[:10]] -= 1; load[nvd] += 1
                        p.at[victim, c] = nvd
                moved.append((p.at[victim, 'target_id'], p.at[victim, 'Company'],
                              d.isoformat(), vd.isoformat() + '  (displaced)'))
            shift = (d - date.fromisoformat(old)).days
            firsts[old] -= 1; firsts[d.isoformat()] += 1
            day_firms[d.isoformat()].add(key)
            for c in ('touch1_date', 'touch2_date', 'touch3_date'):
                v = p.at[i, c]
                if isinstance(v, str) and v:
                    nvd = nb(date.fromisoformat(str(v)[:10]) + timedelta(days=shift)).isoformat()
                    load[str(v)[:10]] -= 1; load[nvd] += 1
                    p.at[i, c] = nvd
            moved.append((p.at[i, 'target_id'], shown, old, d.isoformat()))

    for t, co, old, new in moved:
        print(f'  {t}  {co[:34]:34}  {old} -> {new}')
    if not moved:
        print('every colleague at those firms is already inside the window')
    elif apply:
        p.to_csv(paths.s(paths.PLAN), index=False)
        print(f'\napplied: {len([m for m in moved if m[3][0].isdigit()])} rows pulled forward. '
              'Rebuild the folder so the desk sees them: make folder')
    else:
        print(f'\ndry run: {len(moved)} rows. Add --apply to write, then: make folder')
    return 0

if __name__ == '__main__':
    sys.exit(main())
