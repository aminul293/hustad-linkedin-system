"""
Select the 3-week new-business target set and assign send dates.
Plan: Week 1 ramp 15/20/25/25/15 = 100 new; Week 2 (Labor Day Mon) 8/8/8/6 = 30; Week 3 8/6/6/6/4 = 30.
Total 160 primary targets + 40 reserve. Touch 2 = +7 calendar days, Touch 3 = +14, rolled to next business day.
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
import pandas as pd, numpy as np
from datetime import date, timedelta

m = pd.read_csv(paths.s(paths.MASTER))
elig = m[m.program_status == 'ELIGIBLE'].copy()

# Segment groups for quotas
def seg_group(s):
    if s in ('Student housing',): return 'Student'
    if s in ('Senior living',): return 'Senior'
    if s in ('Commercial', 'Retail', 'Industrial', 'Multifamily / Commercial', 'Hospitality', 'Healthcare'): return 'Commercial'
    if s in ('HOA / Condo',): return 'HOA'
    if s in ('Affordable multifamily', 'Military housing', 'Build to rent', 'Single family rental', 'Manufactured housing'): return 'Specialty residential'
    return 'Multifamily'
elig['seg_group'] = elig['segment'].map(seg_group)

QUOTA_MIN = {'Student': 14, 'Senior': 12, 'Commercial': 14, 'HOA': 8, 'Specialty residential': 6}
CAP_DEFAULT = 3
CAP_BIG = {'RPM Living': 4, 'Avenue5 Residential': 4, 'Greystar': 4, 'Willow Bridge Property Company': 4}

# Candidate ordering: tier first, then score, then recency
tier_rank = {'T1 Priority': 0, 'T2 High': 1, 'T3 Standard': 2, 'T4 Site level / later': 3}
elig['tier_rank'] = elig['target_tier'].map(tier_rank)
elig = elig.sort_values(['tier_rank', 'icp_score', 'days_since_connected'], ascending=[True, False, True]).reset_index(drop=True)

N_PRIMARY, N_RESERVE = 160, 40
selected = []
company_used = {}

def can_take(row):
    cap = CAP_BIG.get(row['Company'], CAP_DEFAULT)
    return company_used.get(row['Company'], 0) < cap

LANE_MIN = {'Facilities / Maintenance': 26, 'CapEx / Construction': 26, 'Asset management': 26, 'VP / Director Operations': 44,
            'Regional / Portfolio': 12, 'Procurement / Risk': 3, 'Ownership / Executive': 55}
sel_keys = set()
def take(r):
    selected.append(r); sel_keys.add(r['url_key']); company_used[r['Company']] = company_used.get(r['Company'], 0) + 1

# Pass 0: lane quotas (the people who actually own exterior decisions)
for lane_name, q in LANE_MIN.items():
    pool = elig[elig.outreach_lane == lane_name]
    n = 0
    for _, r in pool.iterrows():
        if n >= q: break
        if r['url_key'] in sel_keys or not can_take(r): continue
        take(r); n += 1

# Pass 1: segment quotas from the best available in each group
for grp, q in QUOTA_MIN.items():
    pool = elig[(elig.seg_group == grp)]
    n = sum(1 for s in selected if s['seg_group'] == grp)
    for _, r in pool.iterrows():
        if n >= q: break
        if r['url_key'] in sel_keys or not can_take(r): continue
        take(r); n += 1

# Pass 2: fill to N_PRIMARY + N_RESERVE by overall rank, but hold Ownership/Executive to its quota share
for _, r in elig.iterrows():
    if len(selected) >= N_PRIMARY + N_RESERVE: break
    if r['url_key'] in sel_keys or not can_take(r): continue
    if r['outreach_lane'] == 'Ownership / Executive' and sum(1 for s in selected if s['outreach_lane'] == 'Ownership / Executive') >= 70: continue
    take(r)

sel = pd.DataFrame(selected)
sel = sel.sort_values(['tier_rank', 'icp_score', 'days_since_connected'], ascending=[True, False, True]).reset_index(drop=True)
sel['plan_role'] = ['PRIMARY'] * N_PRIMARY + ['RESERVE'] * (len(sel) - N_PRIMARY)

# Calendar
HOLIDAYS = {date(2026, 9, 7)}
def is_bday(d): return d.weekday() < 5 and d not in HOLIDAYS
def next_bday(d):
    while not is_bday(d): d += timedelta(days=1)
    return d
SEND_DAYS = [
    (date(2026, 8, 31), 15), (date(2026, 9, 1), 20), (date(2026, 9, 2), 25), (date(2026, 9, 3), 25), (date(2026, 9, 4), 15),
    (date(2026, 9, 8), 8), (date(2026, 9, 9), 8), (date(2026, 9, 10), 8), (date(2026, 9, 11), 6),
    (date(2026, 9, 14), 8), (date(2026, 9, 15), 6), (date(2026, 9, 16), 6), (date(2026, 9, 17), 6), (date(2026, 9, 18), 4),
]
assert sum(n for _, n in SEND_DAYS) == N_PRIMARY

# Assign primaries to days: round-robin by lane so each day is mixed, one per company per day
primary = sel[sel.plan_role == 'PRIMARY'].copy()
lanes = primary['outreach_lane'].unique().tolist()
day_slots = [[d, n, []] for d, n in SEND_DAYS]
unassigned = primary.to_dict('records')
di = 0
while unassigned:
    d, n, rows = day_slots[di % len(day_slots)]
    if len(rows) < n:
        # pick first unassigned whose company is not already on this day and whose lane is least represented today
        lane_counts = {}
        for rr in rows: lane_counts[rr['outreach_lane']] = lane_counts.get(rr['outreach_lane'], 0) + 1
        comps_today = set(rr['Company'] for rr in rows)
        cand = [r for r in unassigned if r['Company'] not in comps_today]
        if not cand: cand = unassigned
        cand.sort(key=lambda r: (lane_counts.get(r['outreach_lane'], 0), -r['icp_score']))
        pick = cand[0]
        rows.append(pick); unassigned.remove(pick)
    di += 1
    if all(len(rows) >= n for _, n, rows in day_slots) and unassigned:
        raise RuntimeError('slots exhausted')

recs = []
for d, n, rows in day_slots:
    rows.sort(key=lambda r: -r['icp_score'])
    for i, r in enumerate(rows, 1):
        t1 = d; t2 = d + timedelta(days=7); t3 = d + timedelta(days=14)
        # Labor Day: spread the Monday cohort's touch 2 across Tuesday and Wednesday
        if t2 in HOLIDAYS:
            t2 = t2 + timedelta(days=1 if i % 2 else 2)
        t2 = next_bday(t2); t3 = next_bday(max(t3, t2 + timedelta(days=7)))
        r = dict(r); r.update({'touch1_date': t1, 'touch2_date': t2, 'touch3_date': t3, 'day_seq': i,
                                'week': 1 if d <= date(2026, 9, 4) else (2 if d <= date(2026, 9, 11) else 3)})
        recs.append(r)
plan = pd.DataFrame(recs)
reserve = sel[sel.plan_role == 'RESERVE'].copy()
reserve['touch1_date'] = ''; reserve['touch2_date'] = ''; reserve['touch3_date'] = ''; reserve['day_seq'] = ''; reserve['week'] = 'Reserve'
plan = pd.concat([plan, reserve], ignore_index=True)
plan['target_id'] = ['T%03d' % (i + 1) for i in range(len(plan))]
plan.to_csv(paths.s(paths.PLAN_TARGETS), index=False)

print('Selected:', len(plan), ' primary:', (plan.plan_role == 'PRIMARY').sum(), ' reserve:', (plan.plan_role == 'RESERVE').sum())
print(plan[plan.plan_role == 'PRIMARY'].groupby('touch1_date').size())
print(plan.seg_group.value_counts())
print(plan.outreach_lane.value_counts())
print(plan.target_tier.value_counts())
print('Companies:', plan.Company.nunique())
print(plan.Company.value_counts().head(15))
