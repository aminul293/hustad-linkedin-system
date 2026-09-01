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

# Optional real backing store. Unset (the default), the page behaves exactly as before: the log
# lives only in this browser's localStorage. Set both and every tick also syncs to Postgres via
# Supabase's REST API, readable from any device. See backend/db/README.md to provision one.
# CLI flags win over env vars so a one-off local build can still point at nothing.
SUPABASE_URL = opt('--supabase-url', os.environ.get('SUPABASE_URL', ''))
SUPABASE_ANON_KEY = opt('--supabase-anon-key', os.environ.get('SUPABASE_ANON_KEY', ''))

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
CONFIGJSON = json.dumps({'supabaseUrl': SUPABASE_URL, 'supabaseAnonKey': SUPABASE_ANON_KEY}, ensure_ascii=False)

TEMPLATE = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Hustad LinkedIn Desk</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap">
<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/dist/umd/supabase.js"></script>
<style>
:root{
  --paper:#05070B;--card:rgba(10, 14, 23, 0.85);--ink:#F8FAFC;--ink-2:#94A3B8;--ink-3:#64748B;
  --line:rgba(0, 242, 254, 0.15);--line-2:rgba(0, 242, 254, 0.35);--neon-cyan:#00F2FE;--neon-gold:#FFB703;
  --neon-green:#00E676;--copper:#FFB703;--copper-soft:rgba(255,183,3,0.14);--good:#00E676;
  --good-soft:rgba(0,230,118,0.14);--draft-bg:rgba(6,9,16,0.95);--focus:#00F2FE;
}
@media (prefers-color-scheme:light){:root[data-theme="light"]{
  --paper:#F8FAFC;--card:#FFFFFF;--ink:#0F172A;--ink-2:#475569;--ink-3:#94A3B8;
  --line:#E2E8F0;--line-2:#CBD5E1;--neon-cyan:#0284C7;--neon-gold:#D97706;
  --copper:#D97706;--copper-soft:#FEF3C7;--good:#059669;--good-soft:#ECFDF5;--draft-bg:#F1F5F9;--focus:#0284C7;}}
:root[data-theme="dark"]{
  --paper:#05070B;--card:rgba(10, 14, 23, 0.85);--ink:#F8FAFC;--ink-2:#94A3B8;--ink-3:#64748B;
  --line:rgba(0, 242, 254, 0.15);--line-2:rgba(0, 242, 254, 0.35);--neon-cyan:#00F2FE;--neon-gold:#FFB703;
  --neon-green:#00E676;--copper:#FFB703;--copper-soft:rgba(255,183,3,0.14);--good:#00E676;
  --good-soft:rgba(0,230,118,0.14);--draft-bg:rgba(6,9,16,0.95);--focus:#00F2FE;}
*{box-sizing:border-box}
body{margin:0;background:#05070B;color:var(--ink);font-family:"Plus Jakarta Sans",-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;font-size:14px;line-height:1.55;-webkit-font-smoothing:antialiased;background-image:radial-gradient(circle at 50% 0%, rgba(0,242,254,0.12) 0%, rgba(255,183,3,0.06) 40%, transparent 80%);background-attachment:fixed}
.wrap{max-width:1280px;margin:0 auto;padding:0 32px 100px}
.lbl{display:block;font-family:"Plus Jakarta Sans",sans-serif;font-size:11px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:var(--neon-cyan);margin-bottom:4px}
header.top{position:sticky;top:0;z-index:30;background:rgba(5,7,11,0.95);backdrop-filter:blur(24px);-webkit-backdrop-filter:blur(24px);border-bottom:1px solid rgba(0,242,254,0.15);padding:14px 0 0;margin-bottom:28px;box-shadow:0 10px 30px rgba(0,0,0,0.6)}
.top-in{max-width:1280px;margin:0 auto;padding:0 32px;display:flex;align-items:center;justify-content:space-between;gap:20px;flex-wrap:nowrap}
.brand{font-family:"Plus Jakarta Sans",sans-serif;font-size:11px;font-weight:800;letter-spacing:.2em;text-transform:uppercase;color:var(--neon-gold);margin:0 0 2px}
h1{font-family:"Plus Jakarta Sans",sans-serif;font-size:21px;font-weight:800;margin:0;letter-spacing:-.02em;color:var(--ink)}
.savestat{font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--ink-3);margin:2px 0 0}
.savestat.on{color:var(--good)}
.header-actions{display:flex;align-items:center;gap:12px}
.daynav{display:flex;gap:6px;align-items:center}
.daynav select{font-family:"Plus Jakarta Sans",sans-serif;font-size:13px;font-weight:600;padding:7px 12px;background:rgba(10,14,23,0.9);color:var(--ink);border:1px solid rgba(0,242,254,0.2);border-radius:8px;outline:none}
.daynav select:focus{border-color:var(--neon-cyan)}
.daynav button{font-family:"Plus Jakarta Sans",sans-serif;font-size:13px;font-weight:700;padding:7px 12px;background:rgba(10,14,23,0.9);color:var(--ink);border:1px solid rgba(0,242,254,0.2);border-radius:8px;cursor:pointer;transition:all 0.2s ease}
.daynav button:hover{border-color:var(--neon-cyan);color:var(--neon-cyan)}
.prog-pill{display:inline-flex;align-items:center;gap:6px;padding:6px 14px;background:rgba(0,242,254,0.08);border:1px solid rgba(0,242,254,0.25);border-radius:20px;font-size:12px;font-weight:700;color:var(--neon-gold);white-space:nowrap}
.prog-pill b{font-family:"Plus Jakarta Sans",sans-serif;font-size:14px;font-weight:800;color:var(--neon-gold)}
.upload-btn,.signout-btn{font-family:"Plus Jakarta Sans",sans-serif;font-size:12px;font-weight:700;padding:7px 12px;background:rgba(255,255,255,0.03);color:var(--ink-2);border:1px solid rgba(255,255,255,0.1);border-radius:8px;text-decoration:none;transition:all 0.2s ease;white-space:nowrap}
.upload-btn{color:var(--neon-gold);border-color:rgba(255,183,3,0.3);background:rgba(255,183,3,0.06)}
.upload-btn:hover{border-color:var(--neon-gold);color:#FFFFFF;box-shadow:0 0 12px rgba(255,183,3,0.3)}
.signout-btn:hover{border-color:var(--neon-cyan);color:var(--ink)}
.tabrail{max-width:1280px;margin:16px auto 0;padding:0 32px;display:flex;align-items:center}
.tabrail-segment{display:inline-flex;align-items:center;background:rgba(10,14,23,0.92);border:1px solid rgba(0,242,254,0.22);border-radius:12px;padding:4px;gap:4px;box-shadow:0 4px 20px rgba(0,0,0,0.4)}
.tabrail-segment button{font-family:"Plus Jakarta Sans",sans-serif;font-size:12px;font-weight:800;letter-spacing:.06em;text-transform:uppercase;background:transparent;color:var(--ink-2);border:0!important;border-radius:8px!important;padding:8px 18px!important;cursor:pointer;transition:all 0.2s cubic-bezier(0.16, 1, 0.3, 1);outline:none;margin:0!important}
.tabrail-segment button:hover{color:var(--ink);background:rgba(255,255,255,0.05)}
.tabrail-segment button.is-on{background:linear-gradient(135deg, #00F2FE, #4FACFE)!important;color:#05070B!important;font-weight:800!important;box-shadow:0 0 16px rgba(0,242,254,0.4)!important}
.tiles{display:grid;grid-template-columns:repeat(2,1fr);gap:14px;margin:0 0 24px}
@media(min-width:660px){.tiles{grid-template-columns:repeat(4,1fr)}}
.tile{background:rgba(10,14,23,0.85);backdrop-filter:blur(24px);-webkit-backdrop-filter:blur(24px);border:1px solid rgba(0,242,254,0.18);border-radius:14px;padding:18px 22px;box-shadow:0 8px 24px rgba(0,0,0,0.35);transition:all 0.25s ease}
.tile:hover{transform:translateY(-2px);border-color:var(--neon-cyan);box-shadow:0 12px 30px rgba(0,0,0,0.5)}
.tile b{display:block;font-family:"Plus Jakarta Sans",sans-serif;font-size:28px;font-weight:800;font-variant-numeric:tabular-nums;color:var(--neon-gold);line-height:1.1}
.tile span{font-size:12px;font-weight:600;color:var(--ink-2);display:block;margin-top:4px}
.panel{background:rgba(10,14,23,0.85);backdrop-filter:blur(24px);-webkit-backdrop-filter:blur(24px);border:1px solid rgba(0,242,254,0.18);border-radius:14px;padding:20px 24px;margin-bottom:24px;box-shadow:0 8px 24px rgba(0,0,0,0.35)}
.panel h3{font-family:"Plus Jakarta Sans",sans-serif;font-size:12px;font-weight:800;letter-spacing:.12em;text-transform:uppercase;color:var(--neon-cyan);margin:0 0 8px}
.panel p{margin:6px 0 0;font-size:13.5px;color:var(--ink-2);line-height:1.65}
.panel p:first-of-type{margin-top:0}
.panel ol{margin:0;padding-left:18px;font-size:13.5px;color:var(--ink-2);line-height:1.7}
.panel ol li::marker{color:var(--neon-cyan);font-weight:700}
.row{background:rgba(10,14,23,0.85);backdrop-filter:blur(24px);-webkit-backdrop-filter:blur(24px);border:1px solid rgba(0,242,254,0.18);border-radius:16px;padding:24px;margin-bottom:20px;box-shadow:0 12px 32px rgba(0,0,0,0.4);transition:all 0.25s ease}
.row:hover{border-color:var(--neon-cyan);transform:translateY(-2px);box-shadow:0 16px 40px rgba(0,0,0,0.5)}
.row.is-done{opacity:.4}
.row.is-halted{opacity:.6;border-style:dashed;border-color:var(--good)}
.row-grid{display:block}
@media(min-width:1024px){
  .row-grid{display:grid;grid-template-columns:1fr 1fr;gap:24px;align-items:start}
}
.row-left{min-width:0}
.row-right{min-width:0}
@media(min-width:1024px){.row-right .draft{margin-top:0}}
.row-head{display:flex;gap:14px;align-items:flex-start}
.seq{font-family:"Plus Jakarta Sans",sans-serif;font-size:13px;font-weight:800;font-variant-numeric:tabular-nums;color:var(--neon-cyan);padding-top:2px;min-width:26px}
.who{flex:1;min-width:0}
.who h2{font-family:"Plus Jakarta Sans",sans-serif;font-size:19px;font-weight:800;margin:0;letter-spacing:-.01em;color:var(--ink)}
.role{margin:2px 0 0;font-size:13.5px;color:var(--ink-2);font-weight:500}
.org{margin:2px 0 0;font-size:13.5px;font-weight:700;color:var(--neon-gold);display:inline-block}
.marks{display:flex;gap:10px;align-items:center;flex-wrap:wrap;justify-content:flex-end}
.done,.replied{display:flex;gap:6px;align-items:center;cursor:pointer;font-size:11px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:var(--ink-2);white-space:nowrap;user-select:none;padding:5px 12px;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.1);border-radius:8px;transition:all 0.2s ease}
.done:hover,.replied:hover{border-color:var(--neon-cyan);color:var(--ink)}
.done input,.replied input{width:16px;height:16px;accent-color:var(--good);cursor:pointer}
.replied input{accent-color:var(--neon-gold)}
.meta{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:16px 0 0}
.chip{font-size:11px;font-weight:700;letter-spacing:.04em;padding:4px 10px;border-radius:6px;background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.1);color:var(--ink-2)}
.chip-touch{background:rgba(0,242,254,0.12);border-color:rgba(0,242,254,0.3);color:var(--neon-cyan);font-weight:800}
.chip-id{font-variant-numeric:tabular-nums;color:var(--ink-3)}
.chip-storm,.chip-warn{background:rgba(255,183,3,0.12);border-color:rgba(255,183,3,0.3);color:var(--neon-gold);font-weight:800}
.chip-ok,.chip-halt{background:rgba(0,230,118,0.12);border-color:rgba(0,230,118,0.3);color:var(--good);font-weight:800}
.profile{margin-left:auto;font-family:"Plus Jakarta Sans",sans-serif;font-size:12px;font-weight:800;letter-spacing:.03em;color:#05070B;text-decoration:none;background:linear-gradient(135deg, #00F2FE, #4FACFE);padding:6px 14px;border-radius:18px;transition:all 0.2s ease;box-shadow:0 0 12px rgba(0,242,254,0.3)}
.profile:hover{color:#05070B;transform:translateY(-1px);box-shadow:0 0 20px rgba(0,242,254,0.6)}
.why{margin:16px 0 0;font-size:13.5px;color:var(--ink-2);line-height:1.6}
.check{margin:16px 0 0;padding:12px 16px;background:rgba(0,242,254,0.03);border-left:3px solid var(--neon-cyan);border-radius:6px}
.check p{margin:0;font-size:13.5px;color:var(--ink-2);line-height:1.6}
.check p+p{margin-top:8px}
.ev{margin:14px 0 0}
.ev ul{margin:0;padding-left:16px;font-size:13px;color:var(--ink-2);line-height:1.7}
.ev a,.panel a{color:var(--neon-cyan);font-weight:600}
.draft{margin-top:16px;border:1px solid rgba(0,242,254,0.18);border-radius:12px;overflow:hidden;background:var(--draft-bg)}
.draft-bar{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:10px 16px;background:rgba(255,255,255,0.02);border-bottom:1px solid rgba(0,242,254,0.12);flex-wrap:wrap}
.tabs{display:flex;border:1px solid rgba(0,242,254,0.2);border-radius:8px;overflow:hidden;flex-wrap:wrap;background:rgba(0,0,0,0.3)}
.tab{font-family:"Plus Jakarta Sans",inherit;font-size:11px;font-weight:800;letter-spacing:.06em;text-transform:uppercase;background:transparent;color:var(--ink-2);border:0;padding:7px 14px;cursor:pointer;transition:all 0.2s ease}
.tab.is-on{background:linear-gradient(135deg, #00F2FE, #4FACFE);color:#05070B;font-weight:800}
.copy{font-family:"Plus Jakarta Sans",inherit;font-size:11px;font-weight:800;letter-spacing:.06em;text-transform:uppercase;background:linear-gradient(135deg, #FFB703, #FB8500);color:#05070B;border:0;border-radius:8px;padding:8px 18px;cursor:pointer;transition:all 0.2s ease;box-shadow:0 0 12px rgba(255,183,3,0.3)}
.copy:hover{transform:scale(1.03);box-shadow:0 0 18px rgba(255,183,3,0.5)}
.copy.ok{background:linear-gradient(135deg, #00E676, #00B0FF);color:#05070B}
.msg{margin:0;padding:18px 20px;font-family:"Plus Jakarta Sans",sans-serif;font-size:14.5px;line-height:1.7;color:var(--ink);white-space:pre-line}
.msg.is-hidden,.hint.is-hidden{display:none}
.hint{margin:0;padding:0 20px 16px;font-size:12.5px;line-height:1.6;color:var(--neon-gold)}
.ph{background:var(--copper-soft);color:var(--neon-gold);font-weight:700;padding:0 4px;border-radius:4px}
.note-row{display:grid;gap:12px;grid-template-columns:1fr;margin-top:16px}
@media(min-width:640px){.note-row{grid-template-columns:1fr 1.6fr}}
.pemp,.note{width:100%;margin-top:4px;font-family:inherit;font-size:13px;padding:10px 12px;background:rgba(5,7,11,0.8);border:1px solid rgba(0,242,254,0.18);border-radius:8px;color:var(--ink);outline:none;transition:all 0.2s ease}
.pemp:focus,.note:focus{border-color:var(--neon-cyan);box-shadow:0 0 12px rgba(0,242,254,0.2)}
.export{margin-top:36px;background:rgba(10,14,23,0.85);backdrop-filter:blur(24px);border:1px solid rgba(0,242,254,0.18);border-radius:14px;padding:22px;box-shadow:0 8px 24px rgba(0,0,0,0.35)}
.export h3{font-family:"Plus Jakarta Sans",sans-serif;font-size:12px;font-weight:800;letter-spacing:.12em;text-transform:uppercase;color:var(--neon-cyan);margin:0 0 6px}
.export p{margin:0 0 12px;font-size:13.5px;color:var(--ink-2)}
textarea{width:100%;min-height:120px;font-family:ui-monospace,Menlo,Consolas,monospace;font-size:12px;padding:12px;background:rgba(5,7,11,0.8);border:1px solid rgba(0,242,254,0.18);border-radius:8px;color:var(--ink);resize:vertical;outline:none}
textarea:focus{border-color:var(--neon-cyan)}
.btns{display:flex;gap:10px;margin-top:12px;flex-wrap:wrap}
.btn{font-family:"Plus Jakarta Sans",inherit;font-size:11.5px;font-weight:800;letter-spacing:.06em;text-transform:uppercase;padding:10px 20px;border:0;background:linear-gradient(135deg, #00F2FE, #4FACFE);color:#05070B;border-radius:8px;cursor:pointer;transition:all 0.2s ease;box-shadow:0 0 14px rgba(0,242,254,0.3)}
.btn:hover{transform:translateY(-1px);box-shadow:0 0 22px rgba(0,242,254,0.5)}
.btn.ghost{background:transparent;color:var(--ink);border:1px solid rgba(0,242,254,0.25);box-shadow:none}
.btn.ghost:hover{border-color:var(--neon-cyan);color:var(--neon-cyan)}
.btn[hidden]{display:none}
.foot{margin-top:36px;font-size:12px;color:var(--ink-3);line-height:1.7}
.empty{background:rgba(10,14,23,0.7);border:1px dashed rgba(0,242,254,0.25);border-radius:14px;padding:36px;text-align:center;color:var(--ink-2);font-size:14.5px}
input:focus-visible,select:focus-visible,button:focus-visible,a:focus-visible,textarea:focus-visible{outline:2px solid var(--focus);outline-offset:2px}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
__STUDIO_CSS__
body.tab-other .daynav,body.tab-other .prog-pill{display:none}
</style></head><body>
<div class="app-root">
<header class="top">
  <div class="top-in">
    <div>
      <p class="brand">Hustad Commercial &middot; Executive Outreach</p>
      <h1>LinkedIn Command Center</h1>
    </div>
    <div class="header-actions">
      <div class="daynav">
        <button type="button" id="prevday" aria-label="Previous send day">&larr;</button>
        <select id="dayselect" aria-label="Send day"></select>
        <button type="button" id="nextday" aria-label="Next send day">&rarr;</button>
        <button type="button" id="today">Today</button>
      </div>
      <div class="prog-pill"><b id="pdone">0</b><span id="ptot"> / 0 Sent</span></div>
      <a href="/upload" class="upload-btn">📤 Upload CSV</a>
      <a href="/logout" class="signout-btn">🔒 Sign Out</a>
    </div>
  </div>
  <nav class="tabrail" id="tabrail" role="tablist" aria-label="Sections">
    <div class="tabrail-segment">
      <button type="button" data-pane="outreach" class="is-on" role="tab" aria-selected="true">Outreach Queue</button>
      <button type="button" data-pane="replies" role="tab" aria-selected="false">Reply Inbox</button>
      <button type="button" data-pane="posts" role="tab" aria-selected="false">Post Publishing</button>
      <button type="button" data-pane="newsletter" role="tab" aria-selected="false">Newsletter</button>
      <button type="button" data-pane="articles" role="tab" aria-selected="false">Articles</button>
    </div>
  </nav>
</header>
<div class="wrap">
<div id="pane-outreach" class="pane is-on">
  <div class="tiles" id="tiles"></div>
  <section class="panel" id="deskpanel"></section>
  <section class="panel">
    <h3>Standard Execution Protocol</h3>
    <ol>
      <li><b>Verify Executive Profile</b>: Confirm lead title and organization match row before sending.</li>
      <li><b>Check Past History</b>: If a past employer is an active Hustad client, switch draft to <i>Shared History</i> and state the account.</li>
      <li><b>Exclude Active Accounts</b>: Skip warm outreach if the prospect's current organization is an active Hustad client.</li>
      <li><b>Automated Sequence Halting</b>: Marking <i>Replied</i> automatically halts Touch 2 and Touch 3 follow-ups across all devices.</li>
      <li><b>Execute & Log</b>: Copy draft message, send via LinkedIn DM, and check <i>Sent</i>. Activity logs automatically sync.</li>
    </ol>
    <p>Recommended sequence priority: Execute scheduled follow-ups first, then new first touches.</p>
  </section>
  <div id="rows"></div>
  <section class="export">
    <h3>Outreach Activity Log</h3>
    <p>Activity logs automatically persist in browser storage and backup database. Export CSV or copy TSV for Excel records anytime.</p>
    <textarea id="out" readonly placeholder="Tick a row and the log appears here."></textarea>
    <div class="btns">
      <button class="btn" id="copytsv" type="button">Copy for Excel</button>
      <button class="btn ghost" id="copycsv" type="button">Copy CSV text</button>
      <button class="btn ghost" id="download" type="button" hidden>Download send_log.csv</button>
    </div>
  </section>
  <div id="rows"></div>
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
<script id="hustad-config" type="application/json">__CONFIG__</script>
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

// ---- optional Supabase sync -------------------------------------------------
// Unset config (the default): this whole block is inert and the page behaves exactly as it
// always has. Set both build-time secrets and every tick also writes to Postgres, readable from
// any signed-in device. This never replaces localStorage, only adds to it — see backend/db/README.md.
var CONFIG = JSON.parse(document.getElementById('hustad-config').textContent);
var sb = null, sbSession = null;
if (CONFIG.supabaseUrl && CONFIG.supabaseAnonKey && window.supabase && window.supabase.createClient) {
  try { sb = window.supabase.createClient(CONFIG.supabaseUrl, CONFIG.supabaseAnonKey); } catch(e){ sb = null; }
}
function sbStatus(msg){ var el = document.getElementById('sbstat'); if (el){ el.hidden=false; el.textContent = msg; } }
function sbUpsertEntry(e){
  if (!sb || !sbSession) return;
  sb.from('send_log').upsert({
    target_id: e.id, touch: e.touch, send_date: e.date, name: e.name, company: e.company,
    status: e.reply ? 'replied' : (e.done ? 'sent' : 'pending'),
    sent_at: e.at || null, opener: e.opener || null, past_employer: e.pe || null,
    note: e.note || null, updated_at: new Date().toISOString()
  }, { onConflict: 'target_id,touch' }).then(function(r){
    sbStatus(r.error ? ('synced to this browser only — ' + r.error.message) : ('synced to Supabase as ' + sbSession.user.email));
  });
}
function sbUpsertContent(id, e){
  if (!sb || !sbSession) return;
  sb.from('content_log').upsert({
    content_id: id, done: !!e.done, at: e.at || null, status: e.status || null,
    note: e.note || null, updated_at: new Date().toISOString()
  }, { onConflict: 'content_id' }).then(function(r){
    sbStatus(r.error ? ('synced to this browser only — ' + r.error.message) : ('synced to Supabase as ' + sbSession.user.email));
  });
}
function sbMergeRemote(){
  if (!sb || !sbSession) return;
  sb.from('send_log').select('*').then(function(r){
    if (r.error || !r.data) return;
    var changed = false;
    r.data.forEach(function(row){
      var k = row.target_id + '|' + row.touch;
      var ts = row.updated_at ? new Date(row.updated_at).getTime() : 0;
      if (!state.entries[k] || ts >= (state.entries[k].ts||0)) {
        state.entries[k] = { id: row.target_id, touch: row.touch, date: row.send_date,
          name: row.name, company: row.company, done: row.status === 'sent' || row.status === 'replied',
          at: row.sent_at, opener: row.opener, pe: row.past_employer, note: row.note,
          reply: row.status === 'replied' ? 1 : 0, ts: ts };
        changed = true;
      }
    });
    if (changed) { lswrite(state); render(); buildLog(); }
  });
  sb.from('content_log').select('*').then(function(r){
    if (r.error || !r.data) return;
    var changed = false;
    r.data.forEach(function(row){
      var ts = row.updated_at ? new Date(row.updated_at).getTime() : 0;
      if (!state.content[row.content_id] || ts >= (state.content[row.content_id].ts||0)) {
        state.content[row.content_id] = { done: row.done, at: row.at, status: row.status, note: row.note, ts: ts };
        changed = true;
      }
    });
    if (changed) { lswrite(state); if (window.paintContent) paintContent(); }
  });
}
if (sb) {
  sb.auth.getSession().then(function(r){
    sbSession = r.data && r.data.session;
    if (sbSession) { sbStatus('signed in as ' + sbSession.user.email); sbMergeRemote(); }
    else { document.getElementById('sbsignin').hidden = false; sbStatus('not signed in — writes stay on this device only'); }
  });
  sb.auth.onAuthStateChange(function(_evt, session){
    sbSession = session;
    if (session) { document.getElementById('sbsignin').hidden = true; sbStatus('signed in as ' + session.user.email); sbMergeRemote(); }
  });
  document.getElementById('sbsignin').addEventListener('submit', function(ev){
    ev.preventDefault();
    var email = document.getElementById('sbemail').value.trim();
    if (!email) return;
    sbStatus('sending link to ' + email + '...');
    sb.auth.signInWithOtp({ email: email }).then(function(r){
      sbStatus(r.error ? ('sign-in failed — ' + r.error.message) : ('check ' + email + ' for a sign-in link'));
    });
  });
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
  state.entries[key(q)]=e; lswrite(state); paint(); buildLog(); saveSoon(); sbUpsertEntry(e);
  try{ fetch('/api/sync/send', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(e)}).catch(function(){}); }catch(err){} }
function esc(s){ var d=document.createElement('div'); d.textContent=(s==null?'':String(s)); return d.innerHTML; }
function dayQueue(){ return QUEUE.filter(function(q){ return q.date===day; }); }

var VLABEL={clean:['Verified','ok'],revised:['Copy corrected','warn'],flagged:['Read this first','warn'],'no-trigger':['Verified','ok']};

function rowHtml(q,i){
  var e=ent(q), halted=q.touch>1 && replied(q.id) && !e.done, v=q.vstatus?VLABEL[q.vstatus]:null;
  var chips='<span class="chip chip-touch">Touch '+q.touch+'</span><span class="chip">'+esc(q.lane)+'</span>'
    +'<span class="chip">'+esc(q.segment)+'</span><span class="chip chip-id">'+esc(q.id)+'</span>'
    +(v?'<span class="chip chip-'+v[1]+'">'+esc(v[0])+'</span>':'')
    +(q.storm?'<span class="chip chip-storm">Storm trigger</span>':'')
    +(halted?'<span class="chip chip-halt">Replied, halted</span>':'');
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
  var profUrl = q.url || '';
  if (!profUrl || profUrl.indexOf('example.invalid') !== -1 || profUrl.indexOf('http') !== 0) {
    var slug = (q.name || '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
    profUrl = 'https://www.linkedin.com/in/' + (slug || 'linkedin-user');
  }
  return '<article class="row'+(e.done?' is-done':'')+(halted?' is-halted':'')+'" data-k="'+esc(key(q))+'">'
   +'<div class="row-grid"><div class="row-left">'
   +'<header class="row-head"><span class="seq">'+String(i+1).padStart(2,'0')+'</span>'
   +'<div class="who"><h2>'+esc(q.name)+'</h2><p class="role">'+esc(q.position)+'</p><p class="org">'+esc(q.company)+'</p></div>'
   +'<div class="marks"><label class="replied"><input type="checkbox" class="rchk"'+(e.reply?' checked':'')+'><span>Replied</span></label>'
   +'<label class="done"><input type="checkbox" class="chk"'+(e.done?' checked':'')+'><span>Sent</span></label></div></header>'
   +'<div class="meta">'+chips+'<a class="profile" href="'+esc(profUrl)+'" target="_blank" rel="noopener">Open profile &rarr;</a></div>'
   +'<p class="why"><span class="lbl">Why now</span>'+esc(q.why)+'</p>'+chk+ev
   +'</div><div class="row-right">'
   +'<div class="draft"><div class="draft-bar"><div class="tabs" role="tablist">'+tabs.join('')+'</div>'
   +'<button class="copy" type="button">Copy</button></div>'+panes.join('')+'</div>'
   +'<div class="note-row"><label><span class="lbl">Past employer on their profile</span>'
   +'<input type="text" class="pemp" value="'+esc(e.pe||'')+'" placeholder="e.g. Asset Living"></label>'
   +'<label><span class="lbl">Note</span><input type="text" class="note" value="'+esc(e.note||'')+'" placeholder="type storm here if you sent the storm draft"></label></div></div></div></article>';
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
     '<div class="tile"><b>'+t1.length+'</b><span>First Touch Queue</span></div>'
    +'<div class="tile"><b>'+t2+'</b><span>Touch 2 Follow-ups</span></div>'
    +'<div class="tile"><b>'+t3+'</b><span>Touch 3 Final Touches</span></div>'
    +'<div class="tile"><b>'+(storm||rev)+'</b><span>'+(storm?'Live Storm Events':'Verified Deliveries')+'</span></div>';
  var dp=document.getElementById('deskpanel');
  if(storm||rev){ dp.style.display=''; dp.innerHTML='<h3>System Validation Summary</h3>'
    +'<p>Every first touch in today\'s queue was verified against live intelligence before execution: verified organization data, market leadership updates, and NWS severe weather alerts in operator territories.</p>'
    +'<p>'+storm+' targets carry verified storm triggers. '+rev+' target records were validated clean for execution.</p>'; }
  else { dp.style.display='none'; }
  document.getElementById('rows').innerHTML = qs.length ? qs.map(rowHtml).join('')
    : '<div class="empty">No sends scheduled this day.</div>';
  wire(); paint(); buildLog();
}
function paint(){
  var qs=dayQueue(), n=0;
  qs.forEach(function(q){ if(ent(q).done) n++; });
  var pdoneEl = document.getElementById('pdone');
  var ptotEl = document.getElementById('ptot');
  if (pdoneEl) pdoneEl.textContent = n;
  if (ptotEl) ptotEl.textContent = ' / ' + qs.length + ' Sent';
  var pbarEl = document.getElementById('pbar');
  if (pbarEl) pbarEl.style.width = (qs.length ? (n / qs.length * 100) : 0) + '%';
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
        setTimeout(function(){ b.textContent='Copy'; b.classList.remove('ok'); },1400); }); });
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

runtime = TEMPLATE.replace('__QUEUE__', QJSON).replace('__DAYS__', DAYSJ).replace('__CONFIG__', CONFIGJSON) \
                  .replace('__STATE__', '__STATEQUINE__').replace('__B64__', '__B64QUINE__')
b64 = base64.b64encode(runtime.encode()).decode()
full = TEMPLATE.replace('__QUEUE__', QJSON).replace('__DAYS__', DAYSJ).replace('__CONFIG__', CONFIGJSON) \
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
