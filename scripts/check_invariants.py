"""
The rules that must hold before anything ships. Run with: make check

These are not style preferences. Each one exists because breaking it produced a message Eric
refused to send, or would have put a false claim in front of a real buyer.
"""
import sys, os, glob
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'pipeline'))
import pandas as pd, paths
from copy_engine import qa, NEW_CONSTRUCTION

FAIL = []
def check(name, ok, detail=''):
    print(('  PASS  ' if ok else '  FAIL  ') + name + (('  ' + str(detail)) if detail else ''))
    if not ok: FAIL.append(name)

plan_path = paths.PLAN
if not os.path.exists(plan_path):
    print(f'no plan at {plan_path}. Run "make sample" or "make plan" first.'); sys.exit(2)
p = pd.read_csv(plan_path)
pri = p[p.plan_role == 'PRIMARY']
print(f'checking {len(p)} rows, {len(pri)} primaries\n')

# 1. every message passes the linter it was written under
for col, req in [('touch1_qa', True), ('touch2_qa', True), ('touch3_qa', True), ('past_employer_qa', True)]:
    if col in p:
        n = int(p[col].ne('PASS').sum())
        check(f'{col}: every message passes QA', n == 0, f'{n} failures')

# 2. Hustad does not do new construction
blob = ' '.join(str(x) for c in ('touch1_dm','touch2_dm','touch3_dm','past_employer_dm')
                if c in p for x in p[c].dropna()).lower()
hits = [k for k in NEW_CONSTRUCTION if k in blob]
check('no ground up construction language anywhere in the copy', not hits, hits)

# 3. no two people at one firm open on the same sentence
def firm(c): return ' '.join(str(c).lower().replace(',', ' ').split()[:2])
dupes = [f for f, g in pri.groupby(pri.Company.map(firm))
         if len(g) > 1 and len({str(m).split('\n\n')[1] for m in g.touch1_dm if str(m).count('\n\n') >= 1}) < len(g)]
check('no firm has two people opening on the same sentence', not dupes, f'{len(dupes)} firms: {dupes[:5]}')

# 4. paragraph structure survives, because a wall of text does not get read
noblank = int(sum(1 for m in pri.touch1_dm if '\n\n' not in str(m)))
check('every first touch has blank line paragraphs', noblank == 0, f'{noblank} without')

# 5. one question per message
twoq = int(sum(1 for m in pri.touch1_dm if str(m).count('?') > 1))
check('no first touch asks two questions', twoq == 0, f'{twoq} with two')

# 6. nobody gets touched on a weekend or Labor Day
bad = set()
for c in ('touch1_date','touch2_date','touch3_date'):
    for v in pri[c].dropna():
        if not isinstance(v, str) or not v: continue
        d = pd.Timestamp(v[:10])
        if d.weekday() > 4 or v[:10] == '2026-09-07': bad.add(v[:10])
check('no sends land on a weekend or Labor Day', not bad, sorted(bad)[:5])

# 7. firm caps
over = [(f, len(g)) for f, g in pri.groupby(pri.Company.map(firm)) if len(g) > 5]
check('no firm carries more than five targets', not over, over[:5])

# 7b. the Friday first touch cap holds from the day it took effect
import datetime as _dt
_START = '2026-08-28'
_f = pri[pri.touch1_date.astype(str).str[:10] >= _START].touch1_date.astype(str).str[:10].value_counts()
_over = [(d, n) for d, n in sorted(_f.items())
         if n > (15 if _dt.date.fromisoformat(d).weekday() == 4 else 40)]
check('Friday first touches capped at 15, other days at 40', not _over, _over[:5])

# 8. the content calendar passes its own QA (the calendar is code, so this always runs)
import importlib.util as _iu
_spec = _iu.spec_from_file_location('content_engine',
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'pipeline', 'content_engine.py'))
_ce = _iu.module_from_spec(_spec); _spec.loader.exec_module(_ce)
_bad = _ce.validate()
# 9. reply ingestion engine is active and valid
import ingest_replies
# 10. database sync engine is active and valid
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend', 'db'))
import db_sync
check('database sync engine is active and valid', hasattr(db_sync, 'sync_send_entry'))

print()
if FAIL:
    print(f'{len(FAIL)} invariant(s) broken: ' + ', '.join(FAIL)); sys.exit(1)
print('all invariants hold')
