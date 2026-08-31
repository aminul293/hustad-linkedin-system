"""
Eric sent test batch 2 (the ten written for Aug 27) on Aug 26. Move those ten to Aug 26 as sent,
pull ten forward from Aug 28 to refill Aug 27, recompute follow-ups, and log the sends.
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
import pandas as pd
from datetime import date, timedelta

REF = paths.s(paths.CALENDAR)
HOLIDAYS = {date(2026, 9, 7)}
TEN = ['T004','T005','T006','T007','T009','T011','T012','T013','T014','T015']

def nb(d):
    while d.weekday() > 4 or d in HOLIDAYS: d += timedelta(days=1)
    return d

ref = pd.read_csv(REF, dtype=str)
def set_dates(mask, day, start_seq):
    d = date.fromisoformat(day)
    t2 = nb(d + timedelta(days=7)); t3 = nb(max(d + timedelta(days=14), t2 + timedelta(days=7)))
    idx = ref.index[mask]
    for k, i in enumerate(idx):
        ref.loc[i, ['touch1_date','touch2_date','touch3_date','day_seq']] = [day, str(t2), str(t3), str(start_seq + k)]
        ref.loc[i, 'week'] = '0' if day == '2026-08-26' else '1'

# the ten: sent Aug 26
set_dates(ref.target_id.isin(TEN), '2026-08-26', 5)
# refill Aug 27 with the ten lowest-seq Aug 28 rows
a28 = ref[(ref.touch1_date == '2026-08-28')].sort_values('day_seq')
movers = a28.head(10).target_id.tolist()
set_dates(ref.target_id.isin(movers), '2026-08-27', 1)
# resequence what stays on Aug 28
rest = ref[(ref.touch1_date == '2026-08-28')].sort_values('day_seq')
for k, i in enumerate(rest.index, 1):
    ref.loc[i, 'day_seq'] = str(k)
ref.to_csv(REF, index=False)
pri = ref[ref.plan_role == 'PRIMARY']
print(pri.touch1_date.value_counts().sort_index().to_string())
print('moved to Aug 27:', movers)
