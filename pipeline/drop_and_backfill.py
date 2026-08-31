"""
Remove targets that are not a fit for Hustad and promote reserves into the slots they leave.

Hustad does not do new construction. Anyone whose role is purely ground-up development, and any
company whose only verified activity is a development pipeline, comes out of the program.
Construction titles at owner-operators stay: re-roof and exterior capital on existing occupied
assets is core Hustad work, and the copy for those people says so explicitly.
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
import pandas as pd
from datetime import date, timedelta

PLAN = paths.s(paths.PLAN_TARGETS)
OUT  = paths.s(paths.PLAN_TARGETS)
LOG  = paths.s(paths.WORK / 'plan_change_log_v2.csv')
HOLIDAYS = {date(2026, 9, 7)}
TODAY = date(2026, 8, 26)          # days already worked are never backfilled
CAP_DEFAULT, CAP_BIG = 3, {'RPM Living': 4, 'Avenue5 Residential': 4, 'Greystar': 4, 'Willow Bridge Property Company': 4}

DROP = {
 'T003': 'Pure P3 development. Maslow\'s founded 2024, first project opens 2029, no operating portfolio',
 'T021': 'EVP Development. Ground-up role',
 'T044': 'VP/New Development. Ground-up role',
 'T062': 'VP Operations, New Development. Ground-up role; Coastal Ridge covered by an operations contact instead',
 'T079': 'VP, Director of Development. Ground-up role',
 'T109': 'SVP Development. Ground-up role',
 'T116': 'Senior Director of Portfolio Development. Business development role, not a buyer of roofing',
 'T121': 'VP of New Development. Ground-up role',
 'T135': 'VP of Development at a pure development company. No operating portfolio verified',
 'T149': 'VP of Development and Construction. Self-storage and industrial development only',
 'T184': 'Employer not verified: research found an industrial developer, not a multifamily operator',
}

plan = pd.read_csv(PLAN)
log = []
dropped = plan[plan.target_id.isin(DROP)].copy()
for _, r in dropped.iterrows():
    log.append({'target_id': r['target_id'], 'name': r['full_name'], 'company': r['Company'],
                'position': r['Position'], 'change': 'REMOVED', 'reason': DROP[r['target_id']], 'was': r['plan_role']})
plan = plan[~plan.target_id.isin(DROP)].copy()

def is_bday(d): return d.weekday() < 5 and d not in HOLIDAYS
def next_bday(d):
    while not is_bday(d): d += timedelta(days=1)
    return d

vacated = [(pd.to_datetime(r['touch1_date']).date(), int(r['day_seq'])) for _, r in dropped.iterrows()
           if r['plan_role'] == 'PRIMARY']
primaries = plan[plan.plan_role == 'PRIMARY'].copy()
reserves  = plan[plan.plan_role == 'RESERVE'].copy().sort_values('icp_score', ascending=False)

used = primaries['Company'].value_counts().to_dict()
promoted = []
for d, seq in sorted(vacated):
    if d <= TODAY:
        log.append({'target_id': '', 'name': '', 'company': '', 'position': '', 'change': 'SLOT NOT BACKFILLED',
                    'reason': f'{d} is already sent, the day just runs one short', 'was': ''}); continue
    comps_today = set(primaries[pd.to_datetime(primaries['touch1_date']).dt.date == d]['Company'])
    pick = None
    for i, rr in reserves.iterrows():
        if i in promoted or rr['Company'] in comps_today: continue
        if used.get(rr['Company'], 0) >= CAP_BIG.get(rr['Company'], CAP_DEFAULT): continue
        pick = i; break
    if pick is None:
        log.append({'target_id': '', 'name': '', 'company': '', 'position': '', 'change': 'SLOT LEFT OPEN',
                    'reason': f'no eligible reserve for {d} seq {seq}', 'was': ''}); continue
    rr = reserves.loc[pick].copy()
    t2 = next_bday(d + timedelta(days=7))
    t3 = next_bday(max(d + timedelta(days=14), t2 + timedelta(days=7)))
    rr['plan_role'] = 'PRIMARY'; rr['touch1_date'] = str(d); rr['touch2_date'] = str(t2); rr['touch3_date'] = str(t3)
    rr['day_seq'] = seq
    rr['week'] = 1 if d <= date(2026, 9, 4) else (2 if d <= date(2026, 9, 11) else 3)
    primaries = pd.concat([primaries, rr.to_frame().T], ignore_index=True)
    promoted.append(pick); used[rr['Company']] = used.get(rr['Company'], 0) + 1
    log.append({'target_id': rr['target_id'], 'name': rr['full_name'], 'company': rr['Company'],
                'position': rr['Position'], 'change': 'PROMOTED reserve to primary',
                'reason': f'filled slot vacated on {d} seq {seq}', 'was': 'RESERVE'})
reserves = reserves.drop(index=promoted)

out = pd.concat([primaries.sort_values(['touch1_date', 'day_seq']), reserves], ignore_index=True)
out.to_csv(OUT, index=False)
pd.DataFrame(log).to_csv(LOG, index=False)
print('primaries', (out.plan_role == 'PRIMARY').sum(), 'reserves', (out.plan_role == 'RESERVE').sum())
print(pd.DataFrame(log)[['target_id','name','company','change','reason']].to_string())
