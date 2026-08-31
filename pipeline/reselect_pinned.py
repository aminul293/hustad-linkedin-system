"""
Pinned re-selection: keep the existing plan stable, drop rows that are no longer eligible (for example, companies that
appear on the active account list), promote reserves into vacated send slots, and top up reserves from the eligible pool.
Target IDs stay stable; new rows get new IDs. Writes plan_targets.csv and a change log.
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
import pandas as pd, sys
from datetime import date, timedelta
from hooks import HOOKS

PREV = paths.s(paths.WORK / 'plan_v1_backup.csv')
MASTER = paths.s(paths.MASTER)
OUT = paths.s(paths.PLAN_TARGETS)
LOG = paths.s(paths.WORK / 'plan_change_log.csv')
CAP_DEFAULT, CAP_BIG = 3, {'RPM Living': 4, 'Avenue5 Residential': 4, 'Greystar': 4, 'Willow Bridge Property Company': 4}
N_PRIMARY, N_RESERVE = 160, 54
HOLIDAYS = {date(2026, 9, 7)}

prev = pd.read_csv(PREV)
master = pd.read_csv(MASTER)
status = master.set_index('url_key')[['program_status', 'status_reason']].to_dict('index')

def seg_group(s):
    if s == 'Student housing': return 'Student'
    if s == 'Senior living': return 'Senior'
    if s in ('Commercial', 'Retail', 'Industrial', 'Multifamily / Commercial', 'Hospitality', 'Healthcare'): return 'Commercial'
    if s == 'HOA / Condo': return 'HOA'
    if s in ('Affordable multifamily', 'Military housing', 'Build to rent', 'Single family rental', 'Manufactured housing'): return 'Specialty residential'
    return 'Multifamily'

def is_bday(d): return d.weekday() < 5 and d not in HOLIDAYS
def next_bday(d):
    while not is_bday(d): d += timedelta(days=1)
    return d

log = []
keep, removed = [], []
for _, r in prev.iterrows():
    st = status.get(r['url_key'], {'program_status': 'MISSING', 'status_reason': 'not in export'})
    if st['program_status'] == 'ELIGIBLE':
        keep.append(r)
    else:
        removed.append(r); log.append({'target_id': r['target_id'], 'name': r['full_name'], 'company': r['Company'], 'change': 'REMOVED', 'reason': st['status_reason'], 'was': r['plan_role']})
keep = pd.DataFrame(keep)
# refresh the classification columns from the new master (segment fixes etc. stay as in plan)
mcols = ['icp_score', 'target_tier', 'program_status', 'status_reason', 'active_account_flag', 'active_account_crm', 'active_account_owner']
mm = master.set_index('url_key')
for c in mcols:
    keep[c] = keep['url_key'].map(mm[c])

company_used = keep['Company'].value_counts().to_dict()
def can_take(company):
    return company_used.get(company, 0) < CAP_BIG.get(company, CAP_DEFAULT)

# Vacated primary slots
vacated = [(pd.to_datetime(r['touch1_date']).date(), int(r['day_seq'])) for r in removed if r['plan_role'] == 'PRIMARY']
primaries = keep[keep.plan_role == 'PRIMARY'].copy()
reserves = keep[keep.plan_role == 'RESERVE'].copy().sort_values('icp_score', ascending=False)
promoted_idx = []
for d, seq in sorted(vacated):
    comps_today = set(primaries[pd.to_datetime(primaries['touch1_date']).dt.date == d]['Company'])
    pick = None
    for i, r in reserves.iterrows():
        if i in promoted_idx or r['Company'] in comps_today: continue
        pick = i; break
    if pick is None: continue
    r = reserves.loc[pick].copy()
    t2 = d + timedelta(days=7)
    if t2 in HOLIDAYS: t2 += timedelta(days=1 if seq % 2 else 2)
    t2 = next_bday(t2); t3 = next_bday(max(d + timedelta(days=14), t2 + timedelta(days=7)))
    r['plan_role'] = 'PRIMARY'; r['touch1_date'] = d; r['touch2_date'] = t2; r['touch3_date'] = t3; r['day_seq'] = seq
    r['week'] = 1 if d <= date(2026, 9, 4) else (2 if d <= date(2026, 9, 11) else 3)
    primaries = pd.concat([primaries, r.to_frame().T], ignore_index=True)
    promoted_idx.append(pick)
    log.append({'target_id': r['target_id'], 'name': r['full_name'], 'company': r['Company'], 'change': 'PROMOTED reserve to primary', 'reason': f'filled vacated slot {d} seq {seq}', 'was': 'RESERVE'})
reserves = reserves.drop(index=promoted_idx)

# Top up reserves from the eligible pool: prefer researched companies (in HOOKS), then score
in_plan = set(primaries['url_key']) | set(reserves['url_key'])
elig = master[(master.program_status == 'ELIGIBLE') & (~master['url_key'].isin(in_plan))].copy()
elig['researched'] = elig['Company'].isin(HOOKS.keys()).astype(int)
tier_rank = {'T1 Priority': 0, 'T2 High': 1, 'T3 Standard': 2, 'T4 Site level / later': 3}
elig['tier_rank'] = elig['target_tier'].map(tier_rank)
elig = elig[elig.tier_rank <= 1].sort_values(['researched', 'tier_rank', 'icp_score', 'days_since_connected'], ascending=[False, True, False, True])
next_id = int(prev['target_id'].str[1:].astype(int).max()) + 1
new_rows = []
for _, r in elig.iterrows():
    if len(reserves) + len(new_rows) >= N_RESERVE: break
    if not can_take(r['Company']): continue
    if r['role_seniority'] in ('Site Manager (PM/CM/GM)', 'Site Staff / Individual Contributor'): continue
    rr = r.to_dict()
    rr.update({'seg_group': seg_group(r['segment']), 'tier_rank': tier_rank[r['target_tier']], 'plan_role': 'RESERVE', 'touch1_date': '', 'touch2_date': '', 'touch3_date': '', 'day_seq': '', 'week': 'Reserve', 'target_id': 'T%03d' % next_id})
    next_id += 1
    company_used[r['Company']] = company_used.get(r['Company'], 0) + 1
    new_rows.append(rr)
    log.append({'target_id': rr['target_id'], 'name': r['full_name'], 'company': r['Company'], 'change': 'ADDED reserve', 'reason': 'researched company' if rr['researched'] else 'RESEARCH NEEDED', 'was': ''})
new_df = pd.DataFrame(new_rows)
plan = pd.concat([primaries.sort_values(['touch1_date', 'day_seq']), reserves, new_df], ignore_index=True)
cols = [c for c in prev.columns if c in plan.columns]
plan = plan[cols + [c for c in plan.columns if c not in cols and c in ('active_account_flag', 'active_account_crm', 'active_account_owner')]]
plan.to_csv(OUT, index=False)
pd.DataFrame(log).to_csv(LOG, index=False)
print('primaries', (plan.plan_role == 'PRIMARY').sum(), 'reserves', (plan.plan_role == 'RESERVE').sum())
print(pd.DataFrame(log).to_string())
print('research needed for:', sorted(set(new_df[new_df.researched == 0]['Company'])) if len(new_df) else [])
