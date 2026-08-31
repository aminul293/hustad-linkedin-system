"""
Rebuild the send calendar after removals, and freeze it.

The per day first touch counts below are the live schedule Eric is already working: a four person
test batch on Aug 26 (one target was pulled and that day is not backfilled, so it runs one short),
then first touches Aug 27 to Sep 16, follow ups at seven and fourteen business days, levelled so no
day exceeds 40 total sends. Any day short of its target count gets filled from reserves.
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
import pandas as pd
from datetime import date, timedelta

PLAN = paths.s(paths.PLAN)
OUT  = paths.s(paths.PLAN_TARGETS)
REF  = paths.s(paths.CALENDAR)
LOG  = paths.s(paths.WORK / 'plan_change_log_v2.csv')
HOLIDAYS = {date(2026, 9, 7)}
CAP_DEFAULT, CAP_BIG = 3, {'RPM Living': 4, 'Avenue5 Residential': 4, 'Greystar': 4, 'Willow Bridge Property Company': 4}
TARGET = {'2026-08-26': 4, '2026-08-27': 10, '2026-08-28': 20, '2026-08-31': 25, '2026-09-01': 25,
          '2026-09-02': 15, '2026-09-03': 8, '2026-09-04': 8, '2026-09-08': 8, '2026-09-09': 6,
          '2026-09-10': 8, '2026-09-11': 6, '2026-09-14': 6, '2026-09-15': 6, '2026-09-16': 4}
DROP = {
 'T003': "Pure P3 development. Maslow's founded 2024, first project opens 2029, no operating portfolio",
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

def nb(d):
    while d.weekday() > 4 or d in HOLIDAYS: d += timedelta(days=1)
    return d

plan = pd.read_csv(PLAN)
log = []
for _, r in plan[plan.target_id.isin(DROP)].iterrows():
    log.append({'target_id': r['target_id'], 'name': r['full_name'], 'company': r['Company'],
                'position': r['Position'], 'change': 'REMOVED', 'reason': DROP[r['target_id']], 'was': r['plan_role']})
plan = plan[~plan.target_id.isin(DROP)].copy()
log.append({'target_id': '', 'name': '', 'company': '', 'position': '', 'change': 'SLOT NOT BACKFILLED',
            'reason': '2026-08-26 was already sent, so that day just runs one short', 'was': ''})

pri = plan[plan.plan_role == 'PRIMARY'].copy()
res = plan[plan.plan_role == 'RESERVE'].copy().sort_values('icp_score', ascending=False)
used = pri['Company'].value_counts().to_dict()
taken = []
for day in sorted(TARGET):
    have = (pri['touch1_date'] == day).sum()
    for _ in range(TARGET[day] - have):
        comps_today = set(pri[pri.touch1_date == day]['Company'])
        pick = None
        for i, rr in res.iterrows():
            if i in taken or rr['Company'] in comps_today: continue
            if used.get(rr['Company'], 0) >= CAP_BIG.get(rr['Company'], CAP_DEFAULT): continue
            pick = i; break
        if pick is None:
            log.append({'target_id': '', 'name': '', 'company': '', 'position': '', 'change': 'SLOT LEFT OPEN',
                        'reason': f'no eligible reserve for {day}', 'was': ''}); continue
        rr = res.loc[pick].copy()
        d = date.fromisoformat(day)
        seq = int(pd.to_numeric(pri[pri.touch1_date == day]['day_seq'], errors='coerce').max() or 0) + 1
        rr['plan_role'] = 'PRIMARY'; rr['touch1_date'] = day; rr['day_seq'] = seq
        rr['touch2_date'] = str(nb(d + timedelta(days=7)))
        rr['touch3_date'] = str(nb(max(d + timedelta(days=14), nb(d + timedelta(days=7)) + timedelta(days=7))))
        rr['week'] = 1 if d <= date(2026, 9, 4) else (2 if d <= date(2026, 9, 11) else 3)
        pri = pd.concat([pri, rr.to_frame().T], ignore_index=True)
        taken.append(pick); used[rr['Company']] = used.get(rr['Company'], 0) + 1
        log.append({'target_id': rr['target_id'], 'name': rr['full_name'], 'company': rr['Company'],
                    'position': rr['Position'], 'change': 'PROMOTED reserve to primary',
                    'reason': f'filled a slot vacated on {day}', 'was': 'RESERVE'})
res = res.drop(index=taken)
for c in ['touch1_date', 'touch2_date', 'touch3_date', 'day_seq']:
    res[c] = ''
res['week'] = 'Reserve'

out = pd.concat([pri.sort_values(['touch1_date', 'day_seq']), res], ignore_index=True)
keep = [c for c in out.columns if not c.startswith(('touch1_dm', 'touch2_dm', 'touch3_dm', 'past_employer',
        'touch1_words', 'touch2_words', 'touch3_words', 'touch1_qa', 'touch2_qa', 'touch3_qa',
        'company_hook', 'why_now', 'overlap_note', 'proof_used', 'give_offered', 'first_name_used',
        'research_confidence', 'company_hq', 'company_type', 'company_scale', 'company_markets',
        'exterior_relevance', 'recent_news', 'sources'))]
out[keep].to_csv(OUT, index=False)
out[['target_id', 'plan_role', 'touch1_date', 'touch2_date', 'touch3_date', 'day_seq', 'week']].to_csv(REF, index=False)
pd.DataFrame(log).to_csv(LOG, index=False)
print('primaries', (out.plan_role == 'PRIMARY').sum(), '| reserves', (out.plan_role == 'RESERVE').sum())
print(out[out.plan_role == 'PRIMARY'].touch1_date.value_counts().sort_index().to_string())
print('frozen calendar written to', REF)
