"""
Repo-relative paths. Every script imports these instead of hardcoding an absolute path, so the
pipeline runs the same on a laptop, in CI, and in a scheduled Claude session.

Layout, all relative to the repo root:
  data/raw/     the LinkedIn export and the CRM opportunity export. Never committed.
  data/work/    intermediate build products: master_contacts, the plan, the copy. Never committed.
  data/out/     deliverables: the desk page, the workbook, the playbook, the folder bundle.
  data/sample/  synthetic records so the repo runs with no real data. Safe to commit.

Override the root with HUSTAD_DATA if you keep data outside the working tree, which is the
recommended setup on a shared machine.
"""
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent

# Two layouts. In the repo, scripts sit in pipeline/ and data sits in data/. In the OneDrive folder
# the scheduled jobs work from, every script and every CSV sits together in one flat directory, and
# there is no repo around it. Detect which one we are in rather than making the caller say.
FLAT = HERE.name != 'pipeline'

ROOT = HERE if FLAT else HERE.parent
DATA = HERE if FLAT else Path(os.environ.get('HUSTAD_DATA', ROOT / 'data'))
if FLAT:
    RAW = WORK = OUT = SAMPLE = PIPELINE = DATA
else:
    RAW, WORK, OUT, SAMPLE = DATA / 'raw', DATA / 'work', DATA / 'out', DATA / 'sample'
    PIPELINE = ROOT / 'pipeline'
# Company research is harvested data, not code: it names executives quoted in public news, and the
# set of companies in it is the target list. Lives under data/, with a synthetic sample to fall back
# on so a fresh clone still runs.
RESEARCH = DATA if FLAT else DATA / 'research'
RESEARCH_SAMPLE = SAMPLE if FLAT else SAMPLE / 'research'
def research(name):
    f = RESEARCH / name
    return f if f.exists() else RESEARCH_SAMPLE / name
if not FLAT:
    for d in (RAW, WORK, OUT):
        d.mkdir(parents=True, exist_ok=True)

PLAN        = WORK / 'plan_with_copy_final.csv'
PLAN_TARGETS= WORK / 'plan_targets.csv'
MASTER      = WORK / 'master_contacts.csv'
CALENDAR    = PIPELINE / 'calendar_ref.csv'   # target_id and dates only, no names: safe to commit
STORM       = WORK / 'storm_openers.py'      # rebuilt daily, names people: never committed
DESK_HTML   = OUT / 'desk.html'
FOLDER      = OUT / 'linkedin_folder'          # mirrors the OneDrive folder

def s(p):
    return str(p)
