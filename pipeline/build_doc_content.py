"""Regenerate doc_content.json, the input to build_playbook.js, from the live modules and plan."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
import json, pandas as pd, collections
from reply_engine import REPLY_CATEGORIES, DECISION_STYLES, BUYER_STATES, QUALIFICATION, HANDOFF, MEETING_SET, REFERRAL_ASKS, OBJECTIONS

B = paths.s(paths.PIPELINE)
old = json.load(open(f'{paths.PIPELINE}/doc_content.json'))
plan = pd.read_csv(f'{paths.PIPELINE}/plan_with_copy_final.csv')
pri = plan[plan.plan_role == 'PRIMARY']

# Twelve worked examples: one per lane, then fill out with the strongest segments, always primaries.
picks, seen_lane, seen_co = [], set(), set()
for _, r in pri.sort_values(['touch1_date', 'day_seq']).iterrows():
    if r['outreach_lane'] in seen_lane or r['Company'] in seen_co: continue
    picks.append(r); seen_lane.add(r['outreach_lane']); seen_co.add(r['Company'])
for seg in ['Student housing', 'Senior living', 'HOA / Condo', 'Retail', 'Multifamily / Commercial', 'Commercial', 'Affordable multifamily']:
    for _, r in pri[pri.segment == seg].sort_values('icp_score', ascending=False).iterrows():
        if r['Company'] in seen_co: continue
        picks.append(r); seen_co.add(r['Company']); break
examples = [{'id': r['target_id'], 'name': r['full_name'], 'company': r['Company'], 'position': r['Position'],
             'lane': r['outreach_lane'], 'segment': r['segment'], 'why_now': r['why_now'],
             't1': r['touch1_dm'], 't2': r['touch2_dm'], 't3': r['touch3_dm'],
             'shared_history': r['past_employer_dm'], 'words': int(r['touch1_words'])} for r in picks[:13]]

load = collections.Counter()
for c in ['touch1_date', 'touch2_date', 'touch3_date']:
    for v in pri[c].dropna(): load[str(v)[:10]] += 1
stats = dict(old['stats'])
stats.update({
 'primaries': int(len(pri)), 'reserves': int((plan.plan_role == 'RESERVE').sum()),
 'companies': int(plan.Company.nunique()), 'messages': int(len(pri) * 3 + (plan.plan_role == 'RESERVE').sum()),
 'max_sends_per_day': int(max(load.values())), 'first_touch_start': str(min(pri.touch1_date.dropna())),
 'first_touch_end': str(max(pri.touch1_date.dropna())), 'last_send_day': str(max(load)),
 'word_ceiling': 90, 'median_words': int(pri.touch1_words.median()),
 'qa_failures': int(sum((plan[c] != 'PASS').sum() for c in ['touch1_qa','touch2_qa','touch3_qa','past_employer_qa'])),
 'removed_development': int(len(pd.read_csv(f'{paths.WORK}/plan_change_log_v2.csv').query("change=='REMOVED'"))),
})
log = pd.concat([pd.read_csv(f'{paths.WORK}/plan_change_log.csv').assign(position=''),
                 pd.read_csv(f'{paths.WORK}/plan_change_log_v2.csv')], ignore_index=True).fillna('')
doc = {
 'replies': REPLY_CATEGORIES, 'styles': DECISION_STYLES, 'states': BUYER_STATES, 'qual': QUALIFICATION,
 'handoff': HANDOFF, 'meeting': MEETING_SET, 'referrals': REFERRAL_ASKS, 'objections': OBJECTIONS,
 'examples': examples, 'stats': stats,
 'change_log': log.to_dict('records'),
 'active_top': old['active_top'], 'verify_list': old['verify_list'],
}
txt = json.dumps(doc, indent=1).replace(': NaN', ': ""')
open(f'{paths.PIPELINE}/doc_content.json', 'w').write(txt)
print('examples', len(examples), '| change log', len(log), '| primaries', stats['primaries'], '| qa fails', stats['qa_failures'])
