"""Rebuild the LinkedIn folder bundle: one CSV per send day, the roster, reserves and the
reference lists. Everything the scheduled tasks read by name."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
import pandas as pd, os, glob, shutil, zipfile
OD = paths.s(paths.FOLDER)
os.makedirs(OD, exist_ok=True)
plan = pd.read_csv(paths.s(paths.PLAN))

for f in glob.glob(f'{paths.FOLDER}/sendqueue_*.csv'): os.remove(f)

COLS = ['Date','TargetID','Touch','TouchType','Name','Company','Position','Lane','Segment',
        'LinkedInURL','WhyNow','Message','SharedHistoryOpener']
def row(r, touch, msg, d):
    return {'Date': d, 'TargetID': r['target_id'], 'Touch': touch,
            'TouchType': {1:'Touch 1 first DM',2:'Touch 2 value follow',3:'Touch 3 close the loop'}[touch],
            'Name': r['full_name'], 'Company': r['Company'], 'Position': r['Position'],
            'Lane': r['outreach_lane'], 'Segment': r['segment'], 'LinkedInURL': r['URL'],
            'WhyNow': r['why_now'], 'Message': msg,
            'SharedHistoryOpener': r['past_employer_dm'] if touch == 1 else ''}

pri = plan[plan.plan_role == 'PRIMARY']
days = sorted(set(pri['touch1_date'].dropna()) | set(pri['touch2_date'].dropna()) | set(pri['touch3_date'].dropna()))
for d in days:
    rows = [row(r, 1, r['touch1_dm'], d) for _, r in pri[pri.touch1_date == d].sort_values('day_seq').iterrows()]
    rows += [row(r, 2, r['touch2_dm'], d) for _, r in pri[pri.touch2_date == d].sort_values('day_seq').iterrows()]
    rows += [row(r, 3, r['touch3_dm'], d) for _, r in pri[pri.touch3_date == d].sort_values('day_seq').iterrows()]
    pd.DataFrame(rows)[COLS].to_csv(f'{paths.FOLDER}/sendqueue_{d}.csv', index=False)

res = plan[plan.plan_role == 'RESERVE']
pd.DataFrame([row(r, 1, r['touch1_dm'], '') for _, r in res.iterrows()])[COLS].to_csv(f'{paths.FOLDER}/sendqueue_reserves.csv', index=False)

roster = plan[['target_id','full_name','first_name_used','Company','Position','outreach_lane','segment',
               'URL','why_now','plan_role','proof_used','give_offered','touch1_date']].copy()
roster.columns = ['TargetID','Name','FirstName','Company','Position','Lane','Segment','LinkedInURL',
                  'WhyNow','PlanRole','ProofUsed','GiveOffered','FirstTouchDate']
roster.to_csv(f'{paths.FOLDER}/targets_roster.csv', index=False)

# working scripts travel with the data so any refresh session can rebuild everything from the folder
import shutil as _sh
B = paths.s(paths.PIPELINE)
for f in ['paths.py', 'classify.py', 'active_accounts.py', 'hooks.py', 'copy_engine.py', 'reply_engine.py',
          'select_targets.py', 'reselect_pinned.py', 'recalendar.py', 'restore_calendar.py',
          'level_calendar.py', 'drop_and_backfill.py', 'build_onedrive.py', 'build_desk.py',
          'scale_plan.py', 'thread_firm.py',
          'build_reply_md.py', 'calendar_ref.csv', 'studio.py', 'content_engine.py']:
    _sh.copy(f'{paths.PIPELINE}/{f}', f'{paths.FOLDER}/{f}')
# The live storm file if this machine has one, otherwise the empty template.
_sh.copy(paths.s(paths.STORM) if paths.STORM.exists() else f'{paths.PIPELINE}/storm_openers.py',
         f'{paths.FOLDER}/storm_openers.py')
# The account map travels with the folder so a refresh session can rebuild Gate G2.
if (paths.WORK / 'account_map.json').exists():
    _sh.copy(paths.s(paths.WORK / 'account_map.json'), f'{paths.FOLDER}/account_map.json')
_sh.copy(paths.s(paths.research('companies_research.json')), f'{paths.FOLDER}/companies_research.json')
# The full plan travels too. paths.py detects the flat folder, so build_desk.py, level_calendar.py
# and the rest run there unchanged: a scheduled session can rebuild the page from the folder alone.
_sh.copy(paths.s(paths.PLAN), f'{paths.FOLDER}/plan_with_copy_final.csv')
# And the content calendar, which the Posts, Newsletter and Articles tabs render from.
if (paths.WORK / 'content_calendar.json').exists():
    _sh.copy(paths.s(paths.WORK / 'content_calendar.json'), f'{paths.FOLDER}/content_calendar.json')
# The standards guide travels too: any scheduled session drafting copy in Eric's name reads it.
for _d in ('CONTENT_STANDARDS.md', 'VOICE_TELLS.md', 'SERVICE_DELIVERY.md', 'CADENCE.md'):
    _f = paths.ROOT / 'docs' / _d
    if _f.exists():
        _sh.copy(paths.s(_f), f'{paths.FOLDER}/{_d}')

z = paths.s(paths.OUT / 'Hustad_LinkedIn_OneDrive_Bundle_v1_9.zip') 
if os.path.exists(z): os.remove(z)
with zipfile.ZipFile(z, 'w', zipfile.ZIP_DEFLATED) as zf:
    for f in sorted(os.listdir(OD)):
        zf.write(os.path.join(OD, f), f)
print(len(days), 'send days |', len(os.listdir(OD)), 'files |', z, os.path.getsize(z), 'bytes')
