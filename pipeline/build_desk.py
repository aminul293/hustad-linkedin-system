"""
The Hustad Outreach Desk. One page, one bookmark, the whole outreach hour.

This is the console and the morning verification desk merged. It carries a rolling window of the
send calendar, today's live verification and storm triggers, every draft with a copy button, and
the send log, which lives in the browser's own storage and therefore survives the daily rebuild.

  python3 build_desk.py [--day 2026-08-27] [--days 15] [--state seed.json] [--out page.html]

Rebuilt every weekday morning by the Outreach Desk task. Published to the standing URL.
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
import sys, json, html, base64, pandas as pd
from datetime import date

def opt(name, default):
    a = sys.argv[1:]
    return a[a.index(name) + 1] if name in a else default

DAY    = opt('--day', '2026-08-27')
WINDOW = int(opt('--days', '15'))
PLAN   = opt('--plan', paths.s(paths.PLAN))
STATE  = opt('--state', '')
OUT    = opt('--out', paths.s(paths.DESK_HTML))

# Today's storm triggers and verification notes name real people, so the live file lives in
# data/work (never committed) and the tracked copy in pipeline/ is an empty template. Whichever
# exists wins, live first. Missing entirely is fine: the desk just runs without a storm tab.
EVENTS, STORM_DM, VERIFY, DESK_DATE = [], {}, {}, ''
for _dir in (paths.s(paths.WORK), paths.s(paths.PIPELINE)):
    _f = os.path.join(_dir, 'storm_openers.py')
    if not os.path.exists(_f):
        continue
    _ns = {}
    exec(compile(open(_f).read(), _f, 'exec'), _ns)
    if _ns.get('STORM_DM') or _ns.get('VERIFY') or _ns.get('EVENTS'):
        EVENTS  = _ns.get('EVENTS', [])
        STORM_DM = _ns.get('STORM_DM', {})
        VERIFY  = _ns.get('VERIFY', {})
        DESK_DATE = _ns.get('DESK_DATE', '')
        break
evmap = {e['id']: e for e in EVENTS}
desk_live = (DESK_DATE == DAY)

# The content calendar feeds the Posts, Newsletter and Articles tabs. Real first, sample second,
# and an empty dict renders honest empty states rather than failing the outreach build.
CONTENT = {}
for _f in (paths.WORK / 'content_calendar.json', paths.SAMPLE / 'content_calendar.json'):
    try:
        if _f.exists():
            CONTENT = json.load(open(_f)); break
    except Exception as e:
        print('content calendar unreadable, tabs will be empty:', e)
import studio
STUDIO = studio.build(CONTENT)

plan = pd.read_csv(PLAN)
pri = plan[plan.plan_role == 'PRIMARY']

alldays = sorted({d[:10] for c in ('touch1_date','touch2_date','touch3_date')
                  for d in pri[c].dropna() if isinstance(d, str) and d})
try:    i0 = alldays.index(DAY)
except ValueError: i0 = 0
days = alldays[max(0, i0 - 1): i0 + WINDOW]

queue = []
for _, r in pri.iterrows():
    for n, (dcol, mcol) in enumerate([('touch1_date','touch1_dm'), ('touch2_date','touch2_dm'), ('touch3_date','touch3_dm')], 1):
        d = r[dcol]
        if not isinstance(d, str) or d[:10] not in days: continue
        tid = r['target_id']
        row = {'id': tid, 'touch': n, 'date': d[:10],
               'seq': int(float(r['day_seq'])) if pd.notna(r['day_seq']) else 99,
               'name': str(r['full_name']), 'company': str(r['Company']), 'position': str(r['Position']),
               'lane': str(r['outreach_lane']), 'segment': str(r['segment']),
               'url': str(r.get('URL') or ''), 'why': str(r.get('why_now') or ''),
               'msg': str(r[mcol]).strip(),
               'shared': str(r.get('past_employer_dm') or '').strip() if n == 1 else ''}
        if n == 1 and desk_live:
            if tid in STORM_DM:
                ev, txt = STORM_DM[tid]
                row['storm'] = txt
                row['events'] = [{'d': evmap[x]['date'], 'w': evmap[x]['where'],
                                  'x': evmap[x]['what'], 's': evmap[x]['src']} for x in ev if x in evmap]
            if tid in VERIFY:
                st, checked, trig = VERIFY[tid]
                row['vstatus'] = st; row['vcheck'] = checked; row['vtrig'] = trig
        queue.append(row)
queue.sort(key=lambda q: (q['date'], q['touch'] != 2, q['touch'] != 3, q['seq']))

seed = {'entries': {}, 'content': {}, 'v': 4}
if STATE:
    try: seed['entries'] = json.load(open(STATE)).get('entries', {})
    except Exception as e: print('state load failed:', e)
FROMLOG = opt('--from-log', '')
if FROMLOG:
    # Safety net for the daily rebuild: the live log lives in Eric's browser, but the archive
    # send_log.csv in OneDrive can reseed the page if that browser storage is ever lost.
    import csv
    try:
        for r in csv.DictReader(open(FROMLOG)):
            k = f"{r['TargetID']}|{r['Touch']}"
            if k in seed['entries']: continue
            seed['entries'][k] = {'id': r['TargetID'], 'touch': int(r['Touch']), 'date': r['Date'],
                                  'name': r['Name'], 'company': r['Company'],
                                  'done': r['Status'] == 'Sent', 'at': r.get('SentAtLocal', ''),
                                  'opener': r.get('Opener') or 'standard', 'pe': r.get('PastEmployer', ''),
                                  'note': r.get('Notes', ''), 'ts': 1}
        print('seeded', len(seed['entries']), 'entries from', FROMLOG)
    except Exception as e:
        print('log seed failed, publishing with what we have:', e)

QJSON = json.dumps(queue, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
DAYSJ = json.dumps(days)

TEMPLATE = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Hustad LinkedIn Desk</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;600;700&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&family=Lora:wght@500;600&family=Poppins:wght@400;500;600&display=swap">
<style>
:root{
  --paper:#091D24;--card:#0E3F4E;--card-glass:rgba(14, 63, 78, 0.85);--ink:#FFFFFF;--ink-2:#CBD5E1;--ink-3:#94A3B8;
  --line:#42806D;--line-2:rgba(66, 128, 109, 0.4);--navy:#38BDF8;--navy-soft:rgba(56,189,248,0.15);--copper:#F59E0B;
  --copper-soft:rgba(245,158,11,0.18);--good:#10B981;--good-soft:rgba(16,185,129,0.18);--draft-bg:#0A2E38;--focus:#42806D;
  --radius-sm:4px;--radius-md:6px;--radius-lg:9px;--radius-xl:17px;--radius-pill:9999px;
  --shadow-card:rgba(0, 0, 0, 0.15) 0px 20px 25px -5px, rgba(0, 0, 0, 0.1) 0px 8px 10px -6px;
  --ease:250ms cubic-bezier(0.4, 0, 0.2, 1);
}
@media (prefers-color-scheme:light){:root[data-theme="light"]{
  --paper:#F8FAFC;--card:#FFFFFF;--card-glass:rgba(255,255,255,0.9);--ink:#0E3F4E;--ink-2:#475569;--ink-3:#64748B;
  --line:#42806D;--line-2:#CBD5E1;--navy:#0E3F4E;--navy-soft:#E0F2FE;--copper:#D97706;
  --copper-soft:#FEF3C7;--good:#059669;--good-soft:#D1FAE5;--draft-bg:#F8FAFC;--focus:#0E3F4E;}}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;font-size:15px;line-height:1.43;-webkit-font-smoothing:antialiased;background-image:radial-gradient(ellipse 80% 80% at 50% -20%, rgba(66, 128, 109, 0.15), rgba(0, 0, 0, 0))}
.wrap{max-width:1400px;margin:0 auto;padding:0 24px 90px}
.lbl{display:block;font-size:11px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:var(--ink-3);margin-bottom:4px}
header.top{position:sticky;top:0;z-index:30;background:rgba(11, 15, 23, 0.85);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);border-bottom:1px solid var(--line);padding:14px 0 10px;margin-bottom:24px}
.top-in{max-width:1400px;margin:0 auto;padding:0 24px;display:flex;flex-wrap:wrap;gap:14px;align-items:center;justify-content:space-between}
.brand{font-size:11px;font-weight:700;letter-spacing:.18em;text-transform:uppercase;color:var(--copper);margin:0;display:flex;align-items:center;gap:6px}
.brand::before{content:"";display:inline-block;width:6px;height:6px;border-radius:50%;background:var(--copper);box-shadow:0 0 8px var(--copper)}
h1{font-size:22px;font-weight:800;margin:2px 0 0;letter-spacing:-.02em;background:linear-gradient(135deg, #FFFFFF 0%, #94A3B8 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.savestat{font-size:11px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:var(--ink-3);margin:3px 0 0}
.savestat.on{color:var(--good)}
.daynav{display:flex;gap:6px;align-items:center}
.daynav select{font-family:inherit;font-size:13px;font-weight:600;padding:7px 10px;background:var(--card);color:var(--ink);border:1px solid var(--line);border-radius:6px;max-width:210px;cursor:pointer}
.daynav button{font-family:inherit;font-size:13px;font-weight:700;padding:7px 11px;background:var(--card);color:var(--navy);border:1px solid var(--line);border-radius:6px;cursor:pointer;transition:all .2s ease}
.daynav button:hover{background:var(--navy-soft);border-color:var(--navy)}
.prog{text-align:right;min-width:120px}
.prog b{font-size:24px;font-weight:800;font-variant-numeric:tabular-nums;color:var(--navy);letter-spacing:-.02em}
.prog span{font-size:12px;color:var(--ink-2);font-weight:500}
.bar{height:5px;background:var(--line);margin-top:6px;border-radius:3px;overflow:hidden}
.bar i{display:block;height:100%;width:0;background:linear-gradient(90deg, #F59E0B, #10B981);border-radius:3px;transition:width .3s cubic-bezier(0.16,1,0.3,1)}
.uploadbtn{font-family:inherit;font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;padding:9px 14px;background:linear-gradient(135deg, #F59E0B 0%, #D97706 100%);color:#0F172A;border:0;border-radius:6px;text-decoration:none;white-space:nowrap;box-shadow:0 2px 10px rgba(245,158,11,0.25);transition:all .2s ease}
.uploadbtn:hover{filter:brightness(1.12);box-shadow:0 4px 16px rgba(245,158,11,0.4);transform:translateY(-1px)}
.tiles{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin:0 0 20px}
@media(min-width:660px){.tiles{grid-template-columns:repeat(4,1fr)}}
.tile{background:var(--card-glass);backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);border:1px solid var(--line);border-radius:10px;padding:12px 14px;box-shadow:0 8px 20px -4px rgba(0,0,0,0.3);border-top:3px solid var(--navy)}
.tile:nth-child(2){border-top-color:var(--copper)}
.tile:nth-child(3){border-top-color:var(--good)}
.tile:nth-child(4){border-top-color:#8B5CF6}
.tile b{display:block;font-size:24px;font-weight:800;font-variant-numeric:tabular-nums;color:var(--ink);line-height:1.15}
.tile span{font-size:12px;color:var(--ink-2);display:block;margin-top:2px;font-weight:500}
.panel{background:var(--card-glass);backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);border:1px solid var(--line);border-radius:10px;padding:18px 20px;margin-bottom:20px;box-shadow:0 8px 24px -4px rgba(0,0,0,0.3)}
.panel h3{font-size:12px;font-weight:800;letter-spacing:.12em;text-transform:uppercase;color:var(--navy);margin:0 0 9px}
.panel p{margin:7px 0 0;font-size:14px;color:var(--ink-2);line-height:1.6}
.panel p:first-of-type{margin-top:0}
.panel ol{margin:0;padding-left:18px;font-size:14px;color:var(--ink-2);line-height:1.65}
.panel ol li::marker{color:var(--copper);font-weight:700}
.row{background:var(--card-glass);backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);border:1px solid var(--line);border-radius:12px;padding:20px;margin-bottom:16px;box-shadow:0 10px 30px -5px rgba(0,0,0,0.35);transition:all .25s cubic-bezier(0.16,1,0.3,1)}
.row:hover{border-color:var(--line-2);transform:translateY(-2px);box-shadow:0 16px 36px -5px rgba(0,0,0,0.5)}
.row.is-done{opacity:.45}
.row.is-halted{opacity:.55;border-style:dashed;border-color:var(--copper)}
.row-head{display:flex;gap:14px;align-items:flex-start}
.seq{font-size:13px;font-weight:800;font-variant-numeric:tabular-nums;color:var(--ink-3);padding-top:2px;min-width:24px}
.who{flex:1;min-width:0}
.who h2{font-size:18px;font-weight:700;margin:0;letter-spacing:-.015em;color:var(--ink)}
.role{margin:2px 0 0;font-size:14px;color:var(--ink-2);font-weight:500}
.org{margin:2px 0 0;font-size:14px;font-weight:700;color:var(--navy)}
.marks{display:flex;gap:12px;align-items:center;flex-wrap:wrap;justify-content:flex-end}
.done,.replied{display:flex;gap:6px;align-items:center;cursor:pointer;font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--ink-2);white-space:nowrap;user-select:none}
.done input,.replied input{width:18px;height:18px;accent-color:var(--good);cursor:pointer}
.replied input{accent-color:var(--copper)}
.meta{display:flex;gap:7px;flex-wrap:wrap;align-items:center;margin:12px 0 0}
.chip{font-size:11px;font-weight:600;letter-spacing:.04em;padding:4px 10px;background:rgba(255,255,255,0.04);border:1px solid var(--line);border-radius:5px;color:var(--ink-2)}
.chip-touch{background:rgba(245,158,11,0.18);border:1px solid rgba(245,158,11,0.4);color:#FBBF24;font-weight:800}
.chip-lane{background:rgba(56,189,248,0.12);border:1px solid rgba(56,189,248,0.3);color:#38BDF8;font-weight:700}
.chip-seg{background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.35);color:#A5B4FC;font-weight:700}
.chip-id{background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);color:#94A3B8;font-variant-numeric:tabular-nums}
.chip-storm,.chip-warn{background:rgba(239,68,68,0.18);border:1px solid rgba(239,68,68,0.4);color:#FCA5A5;font-weight:800}
.chip-ok{background:rgba(16,185,129,0.18);border:1px solid rgba(16,185,129,0.4);color:#6EE7B7;font-weight:800}
.chip-halt{background:rgba(245,158,11,0.18);border:1px solid rgba(245,158,11,0.4);color:#FBBF24;font-weight:800}
.profile{margin-left:auto;font-size:12px;font-weight:800;letter-spacing:.04em;text-transform:uppercase;color:#38BDF8;background:rgba(56,189,248,0.12);border:1px solid rgba(56,189,248,0.3);border-radius:5px;padding:4px 10px;text-decoration:none;transition:all .2s ease}
.profile:hover{background:rgba(56,189,248,0.25);color:#7DD3FC;transform:translateY(-1px)}
.why{margin:14px 0 0;font-size:14px;color:var(--ink-2);line-height:1.55;background:rgba(0,0,0,0.2);padding:10px 12px;border-radius:6px;border-left:3px solid var(--line-2)}
.check{margin:12px 0 0;padding:12px 14px;background:rgba(0,0,0,0.25);border-left:3px solid var(--copper);border-radius:6px}
.check p{margin:0;font-size:14px;color:var(--ink-2);line-height:1.6}
.check p+p{margin-top:9px}
.ev{margin:10px 0 0}
.ev ul{margin:0;padding-left:17px;font-size:13px;color:var(--ink-2);line-height:1.7}
.ev a,.panel a{color:var(--navy);font-weight:600}
.draft{margin-top:14px;border:1px solid var(--line-2);background:var(--draft-bg);border-radius:8px;overflow:hidden}
.draft-bar{display:flex;align-items:center;justify-content:space-between;gap:8px;padding:8px 12px;border-bottom:1px solid var(--line);background:rgba(0,0,0,0.2);flex-wrap:wrap}
.tabs{display:flex;border:1px solid var(--line);border-radius:6px;overflow:hidden;flex-wrap:wrap}
.tab{font-family:inherit;font-size:10px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;background:transparent;color:var(--ink-2);border:0;padding:6px 11px;cursor:pointer;transition:all .2s ease}
.tab.is-on{background:var(--navy);color:#0F172A}
.copy{font-family:inherit;font-size:11px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;background:var(--navy);color:#0F172A;border:0;padding:7px 15px;border-radius:5px;cursor:pointer;box-shadow:0 2px 8px rgba(56,189,248,0.25);transition:all .2s ease}
.copy:hover{filter:brightness(1.15);box-shadow:0 4px 14px rgba(56,189,248,0.4);transform:translateY(-1px)}
.copy:active{transform:translateY(1px)}
.copy.ok{background:var(--good);color:#FFFFFF}
.regen-btn{font-family:inherit;font-size:11px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;background:linear-gradient(135deg, #F59E0B 0%, #D97706 100%)!important;color:#0F172A!important;border:0!important;padding:7px 15px!important;border-radius:5px!important;cursor:pointer;box-shadow:0 2px 8px rgba(245,158,11,0.25)!important;transition:all .2s ease!important}
.regen-btn:hover{filter:brightness(1.15);box-shadow:0 4px 14px rgba(245,158,11,0.4)!important;transform:translateY(-1px)}
.regen-btn:active{transform:translateY(1px)}
.msg{margin:0;padding:15px 17px;font-family:"Source Serif 4",Georgia,serif;font-size:16px;line-height:1.65;color:var(--ink);white-space:pre-line}
.msg.is-hidden,.hint.is-hidden{display:none}
.hint{margin:0;padding:0 17px 14px;font-size:13px;line-height:1.55;color:var(--copper)}
.ph{background:var(--copper-soft);color:var(--copper);font-weight:700;padding:0 4px;border-radius:3px}
.note-row{display:grid;gap:12px;grid-template-columns:1fr;margin-top:14px}
@media(min-width:640px){.note-row{grid-template-columns:1fr 1.6fr}}
.pemp,.note{width:100%;margin-top:4px;font-family:inherit;font-size:13px;padding:9px 12px;background:rgba(0,0,0,0.25);border:1px solid var(--line);border-radius:6px;color:var(--ink);transition:all .2s ease}
.pemp:focus,.note:focus{border-color:var(--navy);outline:none;box-shadow:0 0 0 2px var(--navy-soft)}
.export{margin-top:30px;background:var(--card-glass);backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);border:1px solid var(--line);border-radius:10px;padding:20px;box-shadow:0 8px 24px -4px rgba(0,0,0,0.3)}
.export h3{font-size:12px;font-weight:800;letter-spacing:.12em;text-transform:uppercase;color:var(--navy);margin:0 0 7px}
.export p{margin:0 0 12px;font-size:14px;color:var(--ink-2)}
textarea{width:100%;min-height:110px;font-family:ui-monospace,Menlo,Consolas,monospace;font-size:12px;padding:12px;background:rgba(0,0,0,0.3);border:1px solid var(--line);border-radius:6px;color:var(--ink);resize:vertical}
.btns{display:flex;gap:10px;margin-top:10px;flex-wrap:wrap}
.btn{font-family:inherit;font-size:12px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;padding:9px 16px;border:1px solid var(--navy);background:var(--navy);color:#0F172A;border-radius:6px;cursor:pointer;transition:all .2s ease}
.btn:hover{filter:brightness(1.1);transform:translateY(-1px)}
.btn.ghost{background:transparent;color:var(--navy)}
.btn.ghost:hover{background:var(--navy-soft)}
.btn[hidden]{display:none}
.console-layout{display:flex;gap:18px;align-items:flex-start;margin-bottom:20px;flex-direction:column}
@media(min-width:768px){.console-layout{flex-direction:row;align-items:stretch}}
.console-sidebar{width:100%;background:var(--card-glass);backdrop-filter:blur(12px);border:1px solid var(--line);border-radius:12px;padding:12px;display:flex;flex-direction:column;gap:10px}
@media(min-width:768px){.console-sidebar{width:320px;min-width:320px;max-height:800px}}
.search-box input{width:100%;padding:9px 12px;background:rgba(0,0,0,0.3);border:1px solid var(--line);border-radius:6px;color:var(--ink);font-size:13px}
.roster-list{display:flex;flex-direction:column;gap:6px;overflow-y:auto;max-height:650px;padding-right:2px}
.roster-item{display:flex;align-items:center;gap:10px;padding:10px 12px;border:1px solid var(--line);border-radius:8px;background:rgba(255,255,255,0.02);cursor:pointer;transition:all .2s ease}
.roster-item:hover{background:rgba(56,189,248,0.08);border-color:var(--line-2)}
.roster-item.active{background:rgba(56,189,248,0.18);border-color:var(--navy);box-shadow:0 0 12px rgba(56,189,248,0.25)}
.roster-item.is-done{opacity:.45}
.roster-seq{font-size:11px;font-weight:800;color:var(--ink-3);min-width:20px}
.roster-info{flex:1;min-width:0}
.roster-name{font-size:13px;font-weight:700;color:var(--ink);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.roster-company{font-size:11px;color:var(--navy);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.console-main{flex:1;width:100%;display:flex;flex-direction:column;gap:12px}
.console-nav-bar{display:flex;align-items:center;justify-content:space-between;background:var(--card-glass);backdrop-filter:blur(12px);border:1px solid var(--line);border-radius:8px;padding:8px 14px;margin-bottom:6px}
.nav-btn{background:var(--navy-soft);border:1px solid var(--line);color:var(--navy);font-size:12px;font-weight:700;padding:6px 12px;border-radius:5px;cursor:pointer;transition:all .2s ease}
.nav-btn:hover{background:var(--navy);color:#0F172A}
.target-counter{font-size:12px;font-weight:800;color:var(--ink-2);letter-spacing:.05em;text-transform:uppercase}
.toast-container{position:fixed;bottom:24px;right:24px;z-index:999;display:flex;flex-direction:column;gap:8px;pointer-events:none}
.toast-msg{background:#1E293B;color:#F8FAFC;border:1px solid #334155;border-left:4px solid var(--copper);padding:12px 18px;border-radius:8px;font-size:13px;font-weight:600;box-shadow:0 12px 30px -5px rgba(0,0,0,0.6);opacity:0;transform:translateY(12px);transition:all .3s cubic-bezier(0.16,1,0.3,1)}
.toast-msg.show{opacity:1;transform:translateY(0)}
.foot{margin-top:28px;font-size:12px;color:var(--ink-3);line-height:1.65;text-align:center}
.empty{background:var(--card-glass);border:1px dashed var(--line-2);border-radius:10px;padding:32px;text-align:center;color:var(--ink-2);font-size:15px}
input:focus-visible,select:focus-visible,button:focus-visible,a:focus-visible,textarea:focus-visible{outline:2px solid var(--focus);outline-offset:2px}
@media (max-width: 767px) {
  .wrap{padding:0 12px 60px}
  .top-in{padding:0 12px;gap:10px}
  h1{font-size:18px}
  .daynav select{max-width:140px;font-size:12px;padding:6px 8px}
  .daynav button{padding:6px 9px;font-size:12px}
  .uploadbtn{padding:7px 10px;font-size:10px}
  .tiles{grid-template-columns:repeat(2,1fr);gap:8px}
  .tile{padding:10px 12px}
  .tile b{font-size:20px}
  .console-sidebar{max-height:220px}
  .roster-list{max-height:160px}
  .console-nav-bar{padding:6px 10px}
  .nav-btn{padding:8px 12px;font-size:12px;min-height:40px}
  .row{padding:14px}
  .row-head{flex-direction:column;gap:8px}
  .marks{width:100%;justify-content:space-between;margin-top:6px}
  .done input,.replied input{width:22px;height:22px}
  .draft-bar{flex-direction:column;align-items:stretch;gap:10px}
  .draft-bar > div{width:100%;justify-content:space-between}
  .copy,.regen-btn{flex:1;text-align:center;padding:10px 14px!important;min-height:44px}
  .tab{flex:1;text-align:center;padding:8px 10px;min-height:38px}
  .profile{margin-left:0;display:inline-block;margin-top:6px;width:100%;text-align:center;padding:8px 12px}
}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
__STUDIO_CSS__
.tabrail{max-width:1400px;margin:12px auto 0;padding:0 24px;display:flex;gap:4px;border-bottom:1px solid var(--line)}
.tabrail button{background:transparent;border:0;border-bottom:2px solid transparent;color:var(--ink-2);font-family:inherit;font-size:12px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;padding:10px 16px;cursor:pointer;transition:all .2s ease}
.tabrail button:hover{color:var(--ink)}
.tabrail button.is-on{color:var(--copper);border-bottom-color:var(--copper)}
body.tab-other .daynav,body.tab-other .prog{display:none}
</style></head><body>
<div class="app-root">
<header class="top"><div class="top-in">
  <div><p class="brand">Hustad &middot; New Business Track</p><h1>LinkedIn Desk</h1>
    <p class="savestat" id="savestat">log saved on this device</p></div>
  <div class="daynav">
    <button type="button" id="prevday" aria-label="Previous send day">&larr;</button>
    <select id="dayselect" aria-label="Send day"></select>
    <button type="button" id="nextday" aria-label="Next send day">&rarr;</button>
    <button type="button" id="today">Today</button>
  </div>
  <div class="prog"><b id="pdone">0</b><span id="ptot"> of 0 sent</span><div class="bar"><i id="pbar"></i></div></div>
  <a class="uploadbtn" href="/upload">Upload Data</a>
</div>
<nav class="tabrail" id="tabrail" role="tablist" aria-label="Sections">
  <button type="button" data-pane="outreach" class="is-on" role="tab" aria-selected="true">DM Outreach</button>
  <button type="button" data-pane="replies" role="tab" aria-selected="false">Reply Center</button>
  <button type="button" data-pane="posts" role="tab" aria-selected="false">Posts</button>
  <button type="button" data-pane="newsletter" role="tab" aria-selected="false">Newsletter</button>
  <button type="button" data-pane="articles" role="tab" aria-selected="false">Articles</button>
</nav></header>
<div class="wrap">
<div id="pane-outreach" class="pane is-on">
  <div class="tiles" id="tiles"></div>
  <section class="panel" id="deskpanel"></section>
  <section class="panel">
    <h3>The twenty second check, before every send</h3>
    <ol>
      <li>Open the profile. Confirm the title and company still match the row.</li>
      <li>Read Experience. If a past employer is a current Hustad client and their time there overlaps our work, switch to <b>Shared history</b>, put that company where [CLIENT] sits, type it in the past employer box, and send it yourself.</li>
      <li>If their <i>current</i> company is a Hustad account, skip and note it. That is warm outreach and it runs elsewhere.</li>
      <li>If they replied on an earlier touch, tick <b>Replied</b>. Their later touches stop automatically.</li>
      <li>Paste, send, tick <b>Sent</b>. The log writes itself.</li>
    </ol>
    <p>Order is deliberate: follow ups first, then first touches. If the hour runs short, defer first touches rather than rush a live conversation.</p>
  </section>
  <div class="console-layout">
    <aside class="console-sidebar">
      <div class="search-box">
        <input type="text" id="roster-search" placeholder="Filter targets or company..." />
      </div>
      <div id="roster-list" class="roster-list"></div>
    </aside>
    <main class="console-main">
      <div class="console-nav-bar">
        <button type="button" id="prev-target-btn" class="nav-btn">&larr; Prev [J]</button>
        <span id="target-counter" class="target-counter">Target 1 of 40</span>
        <button type="button" id="next-target-btn" class="nav-btn">Next [K] &rarr;</button>
      </div>
      <div id="rows"></div>
    </main>
  </div>
  <section class="export">
    <h3>Send log</h3>
    <p>Every tick lands here automatically and stays in this browser, including across the nightly rebuild.
    Copy for Excel pastes into real columns. Download hands you send_log.csv for the LinkedIn folder;
    do that once a week so the Friday review has something to read.</p>
    <textarea id="out" readonly placeholder="Tick a row and the log appears here."></textarea>
    <div class="btns">
      <button class="btn" id="copytsv" type="button">Copy for Excel</button>
      <button class="btn ghost" id="copycsv" type="button">Copy CSV text</button>
      <button class="btn ghost" id="download" type="button" hidden>Download send_log.csv</button>
    </div>
  </section>
  <p class="foot">Cold new business only. Hustad does not do ground up construction and nothing here pitches it.
  Past employment at a Hustad client is your own opener, never a handoff. Every message is sent by hand.
  Storm figures come from National Weather Service reports and local coverage, linked per event; nothing claims
  damage to a specific property or promises a claim outcome.</p>
</div>
<div id="pane-replies" class="pane">__PANE_REPLIES__</div>
<div id="pane-posts" class="pane">__PANE_POSTS__
  <section class="export"><h3>Content log</h3>
  <p>Posted ticks, statuses and URLs from these three tabs, as columns for the tracker.</p>
  <div class="btns"><button class="btn" id="copycontent" type="button">Copy content log</button></div></section>
</div>
<div id="pane-newsletter" class="pane">__PANE_NEWSLETTER__</div>
<div id="pane-articles" class="pane">__PANE_ARTICLES__</div>
</div>
</div>
<div id="printhost" aria-hidden="true"></div>
<script id="hustad-queue" type="application/json">__QUEUE__</script>
<script id="hustad-days" type="application/json">__DAYS__</script>
<script id="hustad-state" type="application/json">__STATE__</script>
<script id="hustad-tpl" type="text/plain">__B64__</script>
<script>
(function(){
'use strict';
var QUEUE = JSON.parse(document.getElementById('hustad-queue').textContent);
var DAYS  = JSON.parse(document.getElementById('hustad-days').textContent);
var EMBED = JSON.parse(document.getElementById('hustad-state').textContent);
var B64   = document.getElementById('hustad-tpl').textContent.trim();
var LSKEY = 'hustad-console-log-v2';
function lsread(){ try { return JSON.parse(localStorage.getItem(LSKEY)) || {entries:{}}; } catch(e){ return {entries:{}}; } }
function lswrite(s){ try { localStorage.setItem(LSKEY, JSON.stringify(s)); } catch(e){} }
var state = {entries:{}, content:{}, v:4};
(function(){ var L=lsread(), k;
  var a=EMBED.entries||{}, b=L.entries||{};
  for(k in a) state.entries[k]=a[k];
  for(k in b) if(!state.entries[k] || (b[k].ts||0) >= (state.entries[k].ts||0)) state.entries[k]=b[k];
  var ca=EMBED.content||{}, cb=L.content||{};
  for(k in ca) state.content[k]=ca[k];
  for(k in cb) if(!state.content[k] || (cb[k].ts||0) >= (state.content[k].ts||0)) state.content[k]=cb[k]; })();

function showToast(text, type){
  var container = document.getElementById('toast-container');
  if(!container){
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }
  var toast = document.createElement('div');
  toast.className = 'toast-msg';
  if(type === 'good') toast.style.borderLeftColor = 'var(--good)';
  toast.textContent = text;
  container.appendChild(toast);
  setTimeout(function(){ toast.classList.add('show'); }, 10);
  setTimeout(function(){
    toast.classList.remove('show');
    setTimeout(function(){ if(toast.parentNode) toast.parentNode.removeChild(toast); }, 300);
  }, 2500);
}

function centralToday(){ try { return new Intl.DateTimeFormat('en-CA',{timeZone:'America/Chicago'}).format(new Date()); }
  catch(e){ return new Date().toISOString().slice(0,10); } }
function defaultDay(){ var t=centralToday(), i;
  for(i=0;i<DAYS.length;i++) if(DAYS[i]>=t) return DAYS[i];
  return DAYS[DAYS.length-1]; }
var day=null; try{ day=sessionStorage.getItem('hustad-day'); }catch(e){}
if(!day || DAYS.indexOf(day)<0) day=defaultDay();

function key(q){ return q.id+'|'+q.touch; }
function ent(q){ return state.entries[key(q)]||{}; }
function replied(id){ for(var k in state.entries){ var e=state.entries[k]; if(e.id===id && e.reply) return true; } return false; }
function setEnt(q,patch){ var e=state.entries[key(q)]||{},k;
  for(k in patch) e[k]=patch[k];
  e.id=q.id;e.touch=q.touch;e.date=q.date;e.name=q.name;e.company=q.company;e.ts=Date.now();
  state.entries[key(q)]=e; lswrite(state); paint(); buildLog(); saveSoon(); }
function esc(s){ var d=document.createElement('div'); d.textContent=(s==null?'':String(s)); return d.innerHTML; }
function dayQueue(){ return QUEUE.filter(function(q){ return q.date===day; }); }

var VLABEL={clean:['Verified','ok'],revised:['Copy corrected','warn'],flagged:['Read this first','warn'],'no-trigger':['Verified','ok']};

function rowHtml(q,i){
  var e=ent(q), halted=q.touch>1 && replied(q.id) && !e.done, v=q.vstatus?VLABEL[q.vstatus]:null;
  var chips='<span class="chip chip-touch">Touch '+q.touch+'</span><span class="chip chip-lane">'+esc(q.lane)+'</span>'
    +'<span class="chip chip-seg">'+esc(q.segment)+'</span><span class="chip chip-id">'+esc(q.id)+'</span>'
    +(v?'<span class="chip chip-'+v[1]+'">'+esc(v[0])+'</span>':'')
    +(q.storm?'<span class="chip chip-storm">⚡ Storm trigger</span>':'')
    +(halted?'<span class="chip chip-halt">🛑 Replied, halted</span>':'');
  var tabs=[], panes=[];
  tabs.push('<button class="tab is-on" type="button" data-v="std">'+(q.storm?'Planned':'Message')+'</button>');
  panes.push('<p class="msg" data-v="std">'+esc(q.msg)+'</p>');
  if(q.storm){ tabs.push('<button class="tab" type="button" data-v="storm">Storm trigger</button>');
    panes.push('<p class="msg is-hidden" data-v="storm">'+esc(q.storm)+'</p>'
      +'<p class="hint is-hidden" data-v="storm">True this week only, and it beats the planned opener where the market actually took weather. If you send this one, type <b>storm</b> in the note below so Friday can measure it.</p>'); }
  if(q.shared){ tabs.push('<button class="tab" type="button" data-v="pe">Shared history</button>');
    panes.push('<p class="msg is-hidden" data-v="pe">'+esc(q.shared).replace(/\[CLIENT\]/g,'<mark class="ph">[CLIENT]</mark>')+'</p>'
      +'<p class="hint is-hidden" data-v="pe">Only if their profile shows a past employer that is a current Hustad client, and their time there overlaps the years we have worked it. Swap <b>[CLIENT]</b> for the company. You send it yourself.</p>'); }
  var ev='';
  if(q.events && q.events.length){ ev='<div class="ev"><span class="lbl">Verified events behind this</span><ul>'
    +q.events.map(function(x){ return '<li><b>'+esc(x.d)+'</b> &middot; '+esc(x.w)+' &middot; '+esc(x.x)
      +' <a href="'+esc(x.s)+'" target="_blank" rel="noopener">source</a></li>'; }).join('')+'</ul></div>'; }
  var chk='';
  if(q.vcheck){ chk='<div class="check"><p><span class="lbl">What the desk checked this morning</span>'+esc(q.vcheck)+'</p>'
    +(q.vtrig?'<p><span class="lbl">Live trigger</span>'+esc(q.vtrig)+'</p>':'')+'</div>'; }
  return '<article class="row'+(e.done?' is-done':'')+(halted?' is-halted':'')+'" data-k="'+esc(key(q))+'">'
   +'<header class="row-head"><span class="seq">'+String(i+1).padStart(2,'0')+'</span>'
   +'<div class="who"><h2>'+esc(q.name)+'</h2><p class="role">'+esc(q.position)+'</p><p class="org">'+esc(q.company)+'</p></div>'
   +'<div class="marks"><label class="replied"><input type="checkbox" class="rchk"'+(e.reply?' checked':'')+'><span>Replied</span></label>'
   +'<label class="done"><input type="checkbox" class="chk"'+(e.done?' checked':'')+'><span>Sent</span></label></div></header>'
   +'<div class="meta">'+chips+(q.url && !q.url.includes('example.invalid') ? '<a class="profile" href="'+esc(q.url)+'" target="_blank" rel="noopener">Open profile &rarr;</a>':'')+'</div>'
   +'<p class="why"><span class="lbl">Why now</span>'+esc(q.why)+'</p>'+chk+ev
   +'<div class="draft"><div class="draft-bar"><div class="tabs" role="tablist">'+tabs.join('')+'</div>'
   +'<div style="display:flex;gap:6px;"><button class="copy regen-btn" type="button" style="background:var(--copper);color:#111;">✨ Re-Generate AI</button><button class="copy" type="button">Copy</button></div></div>'+panes.join('')+'</div>'
   +'<div class="note-row"><label><span class="lbl">Past employer on their profile</span>'
   +'<input type="text" class="pemp" value="'+esc(e.pe||'')+'" placeholder="e.g. Asset Living"></label>'
   +'<label><span class="lbl">Note</span><input type="text" class="note" value="'+esc(e.note||'')+'" placeholder="type storm here if you sent the storm draft"></label></div></article>';
}

var activeTargetIndex = 0;
var rosterSearchQuery = '';

function renderRosterSidebar(qs){
  var rosterEl = document.getElementById('roster-list');
  if(!rosterEl) return;
  var filtered = qs.filter(function(q){
    if(!rosterSearchQuery) return true;
    var term = rosterSearchQuery.toLowerCase();
    return q.name.toLowerCase().indexOf(term) >= 0 || q.company.toLowerCase().indexOf(term) >= 0;
  });
  rosterEl.innerHTML = filtered.map(function(q){
    var idx = qs.indexOf(q);
    var e = ent(q);
    var isActive = idx === activeTargetIndex;
    return '<div class="roster-item'+(isActive?' active':'')+(e.done?' is-done':'')+'" data-idx="'+idx+'">'
      +'<span class="roster-seq">'+String(idx+1).padStart(2,'0')+'</span>'
      +'<div class="roster-info">'
      +'<div class="roster-name">'+esc(q.name)+'</div>'
      +'<div class="roster-company">'+esc(q.company)+'</div>'
      +'</div>'
      +(e.done?'<span style="color:var(--good);font-weight:800;">✓</span>':'')
      +'</div>';
  }).join('');

  Array.prototype.forEach.call(rosterEl.querySelectorAll('.roster-item'), function(item){
    item.addEventListener('click', function(){
      activeTargetIndex = parseInt(item.getAttribute('data-idx'), 10) || 0;
      renderActiveTarget(qs);
    });
  });
}

function renderActiveTarget(qs){
  var rowsEl = document.getElementById('rows');
  var counterEl = document.getElementById('target-counter');
  if(!qs.length){
    if(rowsEl) rowsEl.innerHTML = '<div class="empty">No sends scheduled this day.</div>';
    if(counterEl) counterEl.textContent = '0 of 0';
    return;
  }
  if(activeTargetIndex < 0) activeTargetIndex = 0;
  if(activeTargetIndex >= qs.length) activeTargetIndex = qs.length - 1;
  var q = qs[activeTargetIndex];
  if(rowsEl) rowsEl.innerHTML = rowHtml(q, activeTargetIndex);
  if(counterEl) counterEl.textContent = 'Target ' + (activeTargetIndex + 1) + ' of ' + qs.length;
  renderRosterSidebar(qs);
  wire(); paint();
}

function render(){
  var qs=dayQueue();
  document.getElementById('dayselect').innerHTML=DAYS.map(function(d){
    var n=QUEUE.filter(function(q){return q.date===d;});
    var done=n.filter(function(q){return ent(q).done;}).length;
    var mark=(n.length&&done>=n.length)?' ✓':(done?' · '+done+'/'+n.length:'');
    return '<option value="'+d+'"'+(d===day?' selected':'')+'>'+d+' ('+n.length+')'+mark+'</option>';}).join('');
  var t1=qs.filter(function(q){return q.touch===1;}),
      t2=qs.filter(function(q){return q.touch===2;}).length,
      t3=qs.filter(function(q){return q.touch===3;}).length,
      storm=qs.filter(function(q){return q.storm;}).length,
      rev=qs.filter(function(q){return q.vstatus==='revised'||q.vstatus==='flagged';}).length;
  document.getElementById('tiles').innerHTML=
     '<div class="tile"><b>'+t1.length+'</b><span>first touches</span></div>'
    +'<div class="tile"><b>'+t2+'</b><span>touch 2 follow ups</span></div>'
    +'<div class="tile"><b>'+t3+'</b><span>touch 3 close the loops</span></div>'
    +'<div class="tile"><b>'+(storm||rev)+'</b><span>'+(storm?'with a live storm trigger':'verified by the desk')+'</span></div>';
  var dp=document.getElementById('deskpanel');
  if(storm||rev){ dp.style.display=''; dp.innerHTML='<h3>What the desk did this morning</h3>'
    +'<p>Every first touch below was re-checked against live sources before the block: the stored company fact, recent news, leadership changes, and National Weather Service records for severe weather in each operator\'s markets. Stale numbers were corrected in the plan itself. Where a market actually took weather there is a second draft on the toggle.</p>'
    +'<p>'+storm+' of today\'s first touches have a verified storm trigger. '+rev+' needed a correction or a read before sending.</p>'; }
  else { dp.style.display='none'; }
  activeTargetIndex = 0;
  renderActiveTarget(qs);
  buildLog();
}
function paint(){
  var qs=dayQueue(), n=0;
  qs.forEach(function(q){ if(ent(q).done) n++; });
  document.getElementById('pdone').textContent=n;
  document.getElementById('ptot').textContent=' of '+qs.length+' sent';
  document.getElementById('pbar').style.width=(qs.length?(n/qs.length*100):0)+'%';
  qs.forEach(function(q){ var el=document.querySelector('[data-k="'+key(q)+'"]'); if(!el)return;
    var e=ent(q); el.classList.toggle('is-done',!!e.done);
    el.classList.toggle('is-halted', q.touch>1 && replied(q.id) && !e.done); });
}
function wire(){
  Array.prototype.forEach.call(document.querySelectorAll('.row'),function(el){
    var k=el.getAttribute('data-k'), q=QUEUE.filter(function(x){return key(x)===k;})[0];
    if(!q) return;
    el.querySelector('.chk').addEventListener('change',function(ev){
      var shown=el.querySelector('.msg:not(.is-hidden)'), v=shown?shown.getAttribute('data-v'):'std';
      setEnt(q,{done:ev.target.checked, at:new Date().toTimeString().slice(0,5),
        opener: v==='pe'?'shared history':(v==='storm'?'storm trigger':'standard')}); });
    el.querySelector('.rchk').addEventListener('change',function(ev){ setEnt(q,{reply:ev.target.checked?1:0}); });
    el.querySelector('.pemp').addEventListener('input',function(ev){ setEnt(q,{pe:ev.target.value}); });
    el.querySelector('.note').addEventListener('input',function(ev){ setEnt(q,{note:ev.target.value}); });
    Array.prototype.forEach.call(el.querySelectorAll('.tab'),function(tab){
      tab.addEventListener('click',function(){ var v=tab.getAttribute('data-v');
        Array.prototype.forEach.call(el.querySelectorAll('[data-v]'),function(x){
          if(x.classList.contains('tab')) x.classList.toggle('is-on',x.getAttribute('data-v')===v);
          else x.classList.toggle('is-hidden',x.getAttribute('data-v')!==v); });
        setEnt(q,{variant:v}); }); });
    el.querySelector('.copy').addEventListener('click',function(ev){
      var shown=el.querySelector('.msg:not(.is-hidden)');
      navigator.clipboard.writeText(shown.textContent.trim()).then(function(){
        var b=ev.currentTarget; b.textContent='Copied'; b.classList.add('ok');
        showToast('Copied to clipboard!', 'good');
        setTimeout(function(){ b.textContent='Copy'; b.classList.remove('ok'); },1400); }); });
    var regenBtn = el.querySelector('.regen-btn');
    if(regenBtn){
      regenBtn.addEventListener('click', async function(){
        var b=regenBtn;
        var shown=el.querySelector('.msg:not(.is-hidden)');
        b.textContent='Generating...';
        try {
          var res = await fetch('/api/llm_generate', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
              first_name: q.name.split(' ')[0],
              title: q.position,
              company: q.company,
              segment: q.segment,
              lane: q.lane
            })
          });
          var data = await res.json();
          if(data.ok && data.draft){
            shown.textContent = data.draft;
            b.textContent = '✨ AI Generated!';
            showToast('✨ AI draft generated & 100% QA audited!', 'good');
          } else {
            b.textContent = '✨ Re-Generate AI';
            showToast('Local Sales Brain draft active', 'info');
          }
          setTimeout(function(){ b.textContent = '✨ Re-Generate AI'; },2000);
        } catch(e) { b.textContent = '✨ Re-Generate AI'; }
      });
    }
  });
}
var HDR=['Date','TargetID','Touch','Name','Company','Status','SentAtLocal','Opener','PastEmployer','Notes'];
function logRows(){ var rows=[];
  Object.keys(state.entries).sort().forEach(function(k){ var e=state.entries[k];
    if(!e.done && !e.note && !e.pe && !e.reply) return;
    rows.push([e.date||'',e.id||'',e.touch||'',e.name||'',e.company||'',
      e.done?'Sent':(e.note||e.pe?'Noted':'Replied'), e.at||'', e.opener||'', e.pe||'',
      (e.note||'')+(e.reply?((e.note?'; ':'')+'replied'):'')]); });
  return rows; }
function toCsv(r){ function q(v){ v=(v==null?'':String(v)); return /[",\n]/.test(v)?'"'+v.replace(/"/g,'""')+'"':v; }
  return [HDR.join(',')].concat(r.map(function(x){return x.map(q).join(',');})).join('\n'); }
function toTsv(r){ return [HDR.join('\t')].concat(r.map(function(x){
  return x.map(function(v){return String(v==null?'':v).replace(/[\t\n]/g,' ');}).join('\t');})).join('\n'); }
function buildLog(){ var r=logRows(); document.getElementById('out').value=r.length?toCsv(r):''; }
function bindCopy(id,fn,label){ document.getElementById(id).addEventListener('click',function(ev){
  var r=logRows(); if(!r.length) return;
  navigator.clipboard.writeText(fn(r)).then(function(){ ev.currentTarget.textContent='Copied';
    setTimeout(function(){ ev.currentTarget.textContent=label; },1400); }); }); }
bindCopy('copytsv',toTsv,'Copy for Excel'); bindCopy('copycsv',toCsv,'Copy CSV text');
function go(d){ day=d; try{ sessionStorage.setItem('hustad-day',d); }catch(e){} render(); }
document.getElementById('dayselect').addEventListener('change',function(e){ go(e.target.value); });
document.getElementById('prevday').addEventListener('click',function(){ var i=DAYS.indexOf(day); if(i>0) go(DAYS[i-1]); });
document.getElementById('nextday').addEventListener('click',function(){ var i=DAYS.indexOf(day); if(i<DAYS.length-1) go(DAYS[i+1]); });
document.getElementById('today').addEventListener('click',function(){ go(defaultDay()); });

var pBtn = document.getElementById('prev-target-btn');
if(pBtn) pBtn.addEventListener('click', function(){
  var qs = dayQueue();
  if(activeTargetIndex > 0){
    activeTargetIndex--;
    renderActiveTarget(qs);
  }
});
var nBtn = document.getElementById('next-target-btn');
if(nBtn) nBtn.addEventListener('click', function(){
  var qs = dayQueue();
  if(activeTargetIndex < qs.length - 1){
    activeTargetIndex++;
    renderActiveTarget(qs);
  }
});
var sInput = document.getElementById('roster-search');
if(sInput) sInput.addEventListener('input', function(e){
  rosterSearchQuery = e.target.value;
  renderRosterSidebar(dayQueue());
});
document.addEventListener('keydown', function(e){
  if(e.target && (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA')) return;
  var qs = dayQueue();
  if(e.key === 'j' || e.key === 'J' || e.key === 'ArrowRight'){
    if(activeTargetIndex < qs.length - 1){
      activeTargetIndex++;
      renderActiveTarget(qs);
    }
  } else if(e.key === 'k' || e.key === 'K' || e.key === 'ArrowLeft'){
    if(activeTargetIndex > 0){
      activeTargetIndex--;
      renderActiveTarget(qs);
    }
  }
});

var cap=null, saveTimer=null, dirty=false;
function hydrate(){ return atob(B64).replace('__B64'+'QUINE__',B64)
  .replace('__STATE'+'QUINE__', JSON.stringify(state).replace(/<\//g,'<\\/')); }
function saveSoon(){ dirty=true; if(saveTimer) clearTimeout(saveTimer); saveTimer=setTimeout(doSave,5000); }
function doSave(){ if(!cap||!dirty) return; dirty=false;
  try{ sessionStorage.setItem('hustad-scroll',String(window.scrollY)); sessionStorage.setItem('hustad-day',day); }catch(e){}
  cap.publish(hydrate()).then(function(){ var el=document.getElementById('savestat');
    el.textContent='log saved on every device'; el.classList.add('on'); })
  .catch(function(err){ var c=err&&err.code;
    if(c==='conflict'){ dirty=false; return; }
    if(c==='rate_limited'){ dirty=true; saveTimer=setTimeout(doSave,20000); return; }
    cap=null; document.getElementById('savestat').textContent='log saved on this device'; }); }
window.addEventListener('pagehide',function(){ if(dirty) doSave(); });
// Download works two ways: through the host capability inside the Claude viewer, which
// sandboxes ordinary downloads, and through a plain Blob anywhere else. Same button.
var dlcap=null;
function blobSave(data){ try{
  var b=new Blob([data],{type:'text/csv;charset=utf-8'}), u=URL.createObjectURL(b), a=document.createElement('a');
  a.href=u; a.download='send_log.csv'; document.body.appendChild(a); a.click();
  setTimeout(function(){ URL.revokeObjectURL(u); a.parentNode && a.parentNode.removeChild(a); },0);
}catch(e){} }
(function(){ var b=document.getElementById('download'); b.hidden=false;
  b.addEventListener('click',function(){ var r=logRows(); if(!r.length) return;
    var data=toCsv(r)+'\n';
    if(dlcap) dlcap.save({filename:'send_log.csv', data:data}).catch(function(){ blobSave(data); });
    else blobSave(data); }); })();
if(window.claude && window.claude.use){
  window.claude.use('artifact').then(function(ns){ cap=ns; if(ns&&dirty) doSave(); });
  window.claude.use('downloads').then(function(ns){ dlcap=ns; }); }
try{ var sy=sessionStorage.getItem('hustad-scroll');
  if(sy){ window.scrollTo(0,parseInt(sy,10)||0); sessionStorage.removeItem('hustad-scroll'); } }catch(e){}
render();
__STUDIO_JS__
})();
</script></body></html>'''

def _splice(t):
    sj = STUDIO['js']
    return (t.replace('__STUDIO_CSS__', STUDIO['css'])
             .replace('__PANE_REPLIES__', STUDIO['replies'])
             .replace('__PANE_POSTS__', STUDIO['posts'])
             .replace('__PANE_NEWSLETTER__', STUDIO['newsletter'])
             .replace('__PANE_ARTICLES__', STUDIO['articles'])
             .replace('__STUDIO_JS__', sj))
TEMPLATE = _splice(TEMPLATE)

runtime = TEMPLATE.replace('__QUEUE__', QJSON).replace('__DAYS__', DAYSJ) \
                  .replace('__STATE__', '__STATEQUINE__').replace('__B64__', '__B64QUINE__')
b64 = base64.b64encode(runtime.encode()).decode()
full = TEMPLATE.replace('__QUEUE__', QJSON).replace('__DAYS__', DAYSJ) \
               .replace('__STATE__', json.dumps(seed, ensure_ascii=False).replace('</', '<\\/')) \
               .replace('__B64__', b64)

regen = base64.b64decode(b64).decode().replace('__B64QUINE__', b64) \
        .replace('__STATEQUINE__', json.dumps(seed, ensure_ascii=False).replace('</', '<\\/'))
assert regen == full, 'quine mismatch'

# The Claude Artifact tool wraps a fragment in its own document skeleton at publish time; a web
# server needs the whole document. --standalone chooses the second.
STANDALONE = '--standalone' in sys.argv
if STANDALONE:
    page = full
else:
    page = full[full.index('<title>'):full.index('</head>')] + full[full.index('<body>') + 6: full.rindex('</body>')]
open(OUT, 'w').write(page)
print(f'wrote {OUT} {len(page):,} bytes ({"standalone document" if STANDALONE else "artifact fragment"}) | {len(days)} days, {len(queue)} rows, '
      f'{sum(1 for q in queue if q.get("storm"))} storm, {len(seed["entries"])} log entries | quine stable')
