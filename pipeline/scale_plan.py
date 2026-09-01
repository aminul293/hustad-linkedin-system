"""
Scale the program to 40 first touches a weekday.

Eric has 4,839 connections and 2,709 eligible cold targets outside site level. At 10 a day the
pool takes two years. At 40 a day it takes about seven weeks, which is what he asked for.

Nobody already sent or already scheduled is disturbed. New primaries are drawn Tier 1 first, then
Tier 2, then Tier 3 to fill, under the same company caps and the same rule that two people at one
company never land on the same day. Follow ups keep the seven and fourteen business day spacing.
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
import pandas as pd, collections
from datetime import date, timedelta

B = paths.s(paths.PIPELINE)
PLAN   = paths.s(paths.PLAN)
MASTER = paths.s(paths.MASTER)
OUT    = paths.s(paths.PLAN_TARGETS)
REF    = f'{paths.PIPELINE}/calendar_ref.csv'
LOG    = f'{paths.WORK}/plan_change_log_v3.csv'

PER_DAY   = 40
START     = date(2026, 8, 28)          # today (Aug 27) is already loaded and stays as is
END       = date(2026, 10, 16)
HOLIDAYS  = {date(2026, 9, 7)}
CAP_DEFAULT = 3
CAP_BIG = {'RPM Living': 5, 'Avenue5 Residential': 5, 'Greystar': 5,
           'Willow Bridge Property Company': 5, 'Cushman & Wakefield': 4, 'Asset Living': 4}
SITE = ('Site Manager (PM/CM/GM)', 'Site Staff / Individual Contributor')
TIER_RANK = {'T1 Priority': 0, 'T2 High': 1, 'T3 Standard': 2, 'T4 Site level / later': 3}

def fam(c):
    """Arlington Properties, Inc. and Arlington Properties, LLC are colleagues, not two firms."""
    return ' '.join(str(c).lower().replace(',', ' ').split()[:2])

def is_bd(d): return d.weekday() < 5 and d not in HOLIDAYS
def bdays(a, b):
    out, d = [], a
    while d <= b:
        if is_bd(d): out.append(d)
        d += timedelta(days=1)
    return out
def nb(d):
    while not is_bd(d): d += timedelta(days=1)
    return d

if os.path.exists(PLAN):
    plan = pd.read_csv(PLAN)
elif os.path.exists(f'{paths.SAMPLE}/plan_with_copy_final.csv'):
    plan = pd.read_csv(f'{paths.SAMPLE}/plan_with_copy_final.csv')
else:
    plan = pd.DataFrame(columns=['target_id', 'plan_role', 'touch1_date', 'touch2_date', 'touch3_date', 'day_seq', 'week', 'url_key', 'Company'])
master = pd.read_csv(MASTER)
keep = plan.copy()
pri = keep[keep.plan_role == 'PRIMARY']
in_plan = set(keep['url_key'])
used = collections.Counter(pri['Company'].map(fam))
by_day = collections.defaultdict(set)
for _, r in pri.iterrows():
    if isinstance(r['touch1_date'], str) and r['touch1_date']:
        by_day[r['touch1_date']].add(fam(r['Company']))

# ---- candidate pool, best first
pool = master[(master.program_status == 'ELIGIBLE') & (~master['url_key'].isin(in_plan))].copy()
pool = pool[~pool.role_seniority.isin(SITE)]
pool['tier_rank'] = pool['target_tier'].map(TIER_RANK).fillna(9)
pool = pool[pool.tier_rank <= 2]
pool = pool.sort_values(['tier_rank', 'icp_score', 'days_since_connected'],
                        ascending=[True, False, True]).reset_index(drop=True)
print(f'candidate pool: {len(pool)} across {pool.Company.nunique()} companies')

# ---- days that still need filling
days = bdays(START, END)
need = {}
for d in days:
    k = d.isoformat()
    have = int((pri['touch1_date'] == k).sum())
    if have < PER_DAY: need[k] = PER_DAY - have
print(f'{len(days)} send days, {sum(need.values())} slots to fill')

next_id = int(plan['target_id'].str[1:].astype(int).max()) + 1
rows, log = [], []
pi = 0
for k in sorted(need):
    d = date.fromisoformat(k)
    _mx = pd.to_numeric(pri[pri.touch1_date == k]['day_seq'], errors='coerce').max()
    seq = 0 if pd.isna(_mx) else int(_mx)
    filled = 0
    while filled < need[k] and pi < len(pool):
        r = pool.iloc[pi]; pi += 1
        co = fam(r['Company'])
        if co in by_day[k]: continue                       # never two from one firm in a day
        if used[co] >= CAP_BIG.get(r['Company'], CAP_DEFAULT): continue
        seq += 1; filled += 1
        t2 = nb(d + timedelta(days=7))
        t3 = nb(max(d + timedelta(days=14), t2 + timedelta(days=7)))
        rr = r.to_dict()
        rr.update({'target_id': 'T%04d' % next_id, 'plan_role': 'PRIMARY',
                   'touch1_date': k, 'touch2_date': t2.isoformat(), 'touch3_date': t3.isoformat(),
                   'day_seq': seq, 'week': str(((d - START).days // 7) + 2)})
        next_id += 1; used[co] += 1; by_day[k].add(co)
        rows.append(rr)
    if filled < need[k]:
        log.append({'target_id': '', 'name': '', 'company': '', 'position': '', 'change': 'SHORT DAY',
                    'reason': f'{k} filled {filled} of {need[k]}, pool exhausted under company caps', 'was': ''})

new = pd.DataFrame(rows)
print(f'added {len(new)} primaries; pool consumed {pi} of {len(pool)}')
log.append({'target_id': '', 'name': '', 'company': '', 'position': '', 'change': 'SCALED',
            'reason': f'Raised to {PER_DAY} first touches a weekday, {START} to {END}. Added {len(new)} primaries '
                      f'across {new.Company.nunique() if len(new) else 0} companies. Nobody already sent or scheduled was moved.',
            'was': ''})

if len(keep) > 0 and 'target_id' in keep.columns and len(keep.dropna(subset=['target_id'])) > 0:
    out = pd.concat([keep, new], ignore_index=True)
else:
    out = new

drop = [c for c in out.columns if c.startswith(('touch1_dm','touch2_dm','touch3_dm','past_employer',
        'touch1_words','touch2_words','touch3_words','touch1_qa','touch2_qa','touch3_qa',
        'company_hook','why_now','overlap_note','proof_used','give_offered','first_name_used',
        'research_confidence','company_hq','company_type','company_scale','company_markets',
        'exterior_relevance','recent_news','sources'))]
out.drop(columns=drop, errors='ignore').to_csv(OUT, index=False)
out[['target_id','plan_role','touch1_date','touch2_date','touch3_date','day_seq','week']].to_csv(REF, index=False)
pd.DataFrame(log).to_csv(LOG, index=False)

p2 = out[out.plan_role == 'PRIMARY']
print('\nprimaries now:', len(p2), '| reserves:', (out.plan_role == 'RESERVE').sum(),
      '| companies:', out.Company.nunique())
load = collections.Counter()
for c in ['touch1_date','touch2_date','touch3_date']:
    for v in p2[c].dropna():
        if isinstance(v, str) and v: load[v[:10]] += 1
print('peak total sends in a day:', max(load.values()))
print('\nfirst touches per day:')
print(p2.touch1_date.value_counts().sort_index().to_string())
