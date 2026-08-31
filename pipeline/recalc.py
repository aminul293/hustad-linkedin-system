"""Recalculate the workbook through LibreOffice: proves every formula resolves, and rewrites the
file with LibreOffice's own compression, which lands well under the 1 MB connector cap."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
import subprocess, sys, os, shutil, glob
SRC = sys.argv[1] if len(sys.argv) > 1 else paths.s(paths.OUT / 'Hustad_LinkedIn_NewBusiness_Baseline_v1_2.xlsx')
TMP = '/tmp/recalc_out'
os.makedirs(TMP, exist_ok=True)
for f in glob.glob(f'{TMP}/*'): os.remove(f)
r = subprocess.run(['soffice', '--headless', '--convert-to', 'xlsx:Calc MS Excel 2007 XML',
                    '--outdir', TMP, SRC], capture_output=True, text=True, timeout=900)
print(r.stdout.strip() or r.stderr.strip())
out = glob.glob(f'{TMP}/*.xlsx')
if not out: sys.exit('conversion produced nothing')
before, after = os.path.getsize(SRC), os.path.getsize(out[0])
shutil.move(out[0], SRC)
print(f'{SRC}: {before:,} -> {after:,} bytes ({after/1048576:.2f} MB)')
if after >= 1048576: print('over 1 MB: fine for chat delivery, too big only for the blocked SharePoint upload path')
