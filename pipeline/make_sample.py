"""
Generate a synthetic plan so the repo runs without any real data.

The real plan carries names, titles, companies and LinkedIn URLs for several thousand real people.
None of that belongs in a git repository. This writes a fake plan in the identical schema so a
developer can run build_desk.py, see the page, and iterate on the front end without ever touching
production data.

  python3 pipeline/make_sample.py --out data/sample/plan_with_copy_final.csv
"""
import sys, csv, random
from datetime import date, timedelta

def opt(n, d):
    a = sys.argv[1:]
    return a[a.index(n) + 1] if n in a else d

OUT = opt('--out', 'data/sample/plan_with_copy_final.csv')
N   = int(opt('--rows', '60'))
random.seed(11)

FIRST = ['Dana','Marcus','Priya','Tom','Rosa','Wei','Sam','Nadia','Owen','Claire','Andre','Beth',
         'Hugo','Ivy','Jonah','Kara','Liam','Mona','Nils','Opal','Pete','Quinn','Rhea','Silas']
LAST  = ['Alvarez','Brennan','Chu','Delgado','Ellis','Farkas','Gray','Hollis','Imai','Janssen',
         'Keller','Lindqvist','Moreau','Nakamura','Ortega','Pike','Rourke','Sandoval','Tate','Vogel']
# Enough invented firms that the three per firm cap is never forced to give way.
_STEM = ['Northgate','Brightwater','Cedar Ridge','Halcyon','Ironwood','Juniper','Kestrel','Larkspur',
         'Meridian','Nightfall','Overton','Pinehurst','Quarry Hill','Redbourne','Stonefield','Thornbury',
         'Umberland','Vantage Park','Westmoor','Yarrow','Ashgrove','Bellamy','Coldwater','Dunmore']
_SUFF = ['Residential','Management','Communities','Property Group','Living','Partners']
FIRMS = [f'{a} {b}' for a, b in zip(_STEM, (_SUFF * 5)[:len(_STEM)])]
LANES = ['Ownership / Executive','VP / Director Operations','Regional / Portfolio','Asset management',
         'Facilities / Maintenance','CapEx / Construction','Procurement / Risk']
TITLES = {'Ownership / Executive':'President','VP / Director Operations':'Vice President of Operations',
          'Regional / Portfolio':'Regional Manager','Asset management':'Vice President, Asset Management',
          'Facilities / Maintenance':'Director of Facilities','CapEx / Construction':'Director of Construction',
          'Procurement / Risk':'Director of Procurement'}
SEGS  = ['Multifamily','Student housing','Senior living','HOA / Condo','Retail','Commercial']

HOLIDAYS = {date(2026, 9, 7)}
def bd(d):
    while d.weekday() > 4 or d in HOLIDAYS: d += timedelta(days=1)
    return d

# The sample obeys the same invariants the real plan does, so `make sample && make check` is
# green out of the box and the checker demonstrates what it is protecting.
OPENERS = [
 "Sample opener A: a stand in for one verified fact about their portfolio.",
 "Sample opener B: a stand in for a role truth used when no fact was found.",
 "Sample opener C: a stand in for the budget season question.",
 "Sample opener D: a stand in for an honest note about when we connected.",
 "Sample opener E: a stand in for a segment specific observation.",
]

COLS = ['target_id','plan_role','week','touch1_date','touch2_date','touch3_date','day_seq',
        'full_name','first_name_used','first_name_clean','First Name','Company','Position','URL',
        'Connected On','days_since_connected','outreach_lane','segment','target_tier','icp_score',
        'role_seniority','role_function','company_class','engagement_state','url_key',
        'company_hook','why_now','overlap_note','proof_used','give_offered',
        'touch1_dm','touch1_words','touch1_qa','touch2_dm','touch2_words','touch2_qa',
        'touch3_dm','touch3_words','touch3_qa','past_employer_dm','past_employer_words','past_employer_qa',
        'research_confidence','company_hq','company_type','company_scale','company_markets',
        'exterior_relevance','recent_news','sources','active_account_flag','active_account_crm','active_account_owner']

start = date.today()
rows, seq, day = [], 0, bd(start)
firm_count, firm_openers, day_firms = {}, {}, {}
for i in range(N):
    if seq >= 10:
        seq = 0; day = bd(day + timedelta(days=1))
    seq += 1
    fn, ln = random.choice(FIRST), random.choice(LAST)
    lane = random.choice(LANES); seg = random.choice(SEGS)
    # three per firm, never two from one firm in a day: the real caps
    pool = [f for f in FIRMS if firm_count.get(f, 0) < 3 and f not in day_firms.get(day, set())]
    if not pool:
        seq = 1; day = bd(day + timedelta(days=1))
        pool = [f for f in FIRMS if firm_count.get(f, 0) < 3]
    if not pool:
        break                     # cap reached everywhere; a short sample beats a broken invariant
    firm = random.choice(pool)
    firm_count[firm] = firm_count.get(firm, 0) + 1
    day_firms.setdefault(day, set()).add(firm)
    used = firm_openers.setdefault(firm, set())
    opener = next((o for o in OPENERS if o not in used), OPENERS[0])
    used.add(opener)
    t2 = bd(day + timedelta(days=7)); t3 = bd(max(day + timedelta(days=14), t2 + timedelta(days=7)))
    m1 = (f"Hi {fn},\n\n{opener} No real person, company or fact appears anywhere in this file.\n\n"
          f"Sample second paragraph standing in for what Hustad does for a "
          f"{lane.split(' / ')[0].lower()} contact.\n\nSample closing question?")
    m2 = f"Hi {fn},\n\nSample follow up.\n\nSample evidence line.\n\nSample ask?"
    m3 = f"Hi {fn},\n\nSample close the loop.\n\nSample exit line."
    m4 = (f"Hi {fn},\n\nSample shared history opener mentioning [CLIENT].\n\n"
          f"Did you ever work with anyone from Hustad while you were there?")
    r = {c: '' for c in COLS}
    r.update({'target_id': 'S%03d' % (i + 1), 'plan_role': 'PRIMARY', 'week': '1',
              'touch1_date': day.isoformat(), 'touch2_date': t2.isoformat(), 'touch3_date': t3.isoformat(),
              'day_seq': seq, 'full_name': f'{fn} {ln}', 'first_name_used': fn, 'first_name_clean': fn,
              'First Name': fn, 'Company': firm, 'Position': TITLES[lane],
              'URL': f"https://www.linkedin.com/in/{fn.lower()}-{ln.lower()}",
              'Connected On': (start - timedelta(days=random.randint(30, 400))).isoformat(),
              'days_since_connected': random.randint(30, 400),
              'outreach_lane': lane, 'segment': seg, 'target_tier': 'T1 Priority',
              'icp_score': random.randint(80, 99), 'role_seniority': 'VP', 'role_function': 'Operations',
              'company_class': 'OWNER-OPERATOR', 'engagement_state': 'COLD: no interaction',
              'url_key': f'sample-{i+1}', 'why_now': 'Sample why now line',
              'proof_used': 'Sample Client', 'give_offered': 'the sample one pager',
              'touch1_dm': m1, 'touch1_words': len(m1.split()), 'touch1_qa': 'PASS',
              'touch2_dm': m2, 'touch2_words': len(m2.split()), 'touch2_qa': 'PASS',
              'touch3_dm': m3, 'touch3_words': len(m3.split()), 'touch3_qa': 'PASS',
              'past_employer_dm': m4, 'past_employer_words': len(m4.split()), 'past_employer_qa': 'PASS'})
    rows.append(r)

import os
os.makedirs(os.path.dirname(OUT) or '.', exist_ok=True)
with open(OUT, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=COLS); w.writeheader(); w.writerows(rows)
print(f'wrote {OUT}: {len(rows)} synthetic rows across {len({r["touch1_date"] for r in rows})} days')
