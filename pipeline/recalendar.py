"""
Apply the frozen send calendar (calendar_ref.csv) to plan_targets.csv.

The live calendar (test batch on Aug 26, first touches Aug 27 to Sep 16, follow-ups load leveled
at 40 sends a day around Labor Day) lives in the last shipped plan. This pulls it forward so the
plan file and the shipped queue can never drift apart.
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
import pandas as pd, sys

PLAN = paths.s(paths.PLAN_TARGETS)
CAL  = sys.argv[1] if len(sys.argv) > 1 else paths.s(paths.CALENDAR)
COLS = ['touch1_date', 'touch2_date', 'touch3_date', 'day_seq', 'week']

plan = pd.read_csv(PLAN)
cal  = pd.read_csv(CAL).set_index('target_id')
before = plan[plan.plan_role == 'PRIMARY']['touch1_date'].notna().sum()
for c in COLS:
    plan[c] = plan['target_id'].map(cal[c]).astype(object)
res = plan.plan_role == 'RESERVE'
for c in COLS[:4]:
    plan.loc[res, c] = ''
plan.loc[res, 'week'] = 'Reserve'
plan.to_csv(PLAN, index=False)
p = plan[plan.plan_role == 'PRIMARY']
print('primaries with a date:', p['touch1_date'].notna().sum(), 'of', len(p), '(was', before, ')')
print(p['touch1_date'].value_counts().sort_index().to_string())
