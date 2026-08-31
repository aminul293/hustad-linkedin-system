"""
A web interface for uploading export files and building/viewing the LinkedIn Desk.
Can run locally or hosted (e.g. Render).
"""
import sys, os, subprocess, threading, webbrowser, html, re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import paths  # noqa: E402

PORT = int(os.environ.get('PORT', os.environ.get('HUSTAD_UPLOAD_PORT', '8765')))

RAW_TARGETS = [
    ('Connections.csv',              'a6350e6d-Connections.csv',            'LinkedIn connections export'),
    ('Invitations.csv',              'ff13996e-Invitations.csv',            'LinkedIn invitations export'),
    ('messages.csv',                 '86563516-messages.csv',               'LinkedIn messages export'),
    ('Endorsement_Received_Info.csv', '3da803c8-Endorsement_Received_Info.csv', 'LinkedIn endorsements export'),
    ('opportunities',                'opportunities_2026.csv',              'CRM opportunity export'),
]

def target_for(filename):
    for suffix, dest, label in RAW_TARGETS:
        if filename.lower().endswith(suffix.lower()) or suffix.lower() in filename.lower():
            return dest, label
    return None, None

PAGE = """<!doctype html>
<html><head><meta charset="utf-8"><title>Build the Desk</title>
<style>
  :root{color-scheme:dark light}
  body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#1c1a16;color:#efe8d8;
       max-width:760px;margin:0 auto;padding:40px 24px 80px}
  h1{font-size:26px;margin:0 0 6px}
  p.lede{color:#c7bda6;margin:0 0 32px;max-width:60ch}
  .zone{border:2px dashed #3a3428;border-radius:8px;padding:18px;margin-bottom:14px;
        display:flex;align-items:center;justify-content:space-between;gap:16px;transition:border-color .15s}
  .zone.filled{border-color:#8fbf9f;border-style:solid}
  .zone.drag{border-color:#e3935f}
  .zone-label{font-weight:600}
  .zone-sub{font-size:13px;color:#aab3c0;margin-top:2px}
  .zone-status{font-family:ui-monospace,'JetBrains Mono',monospace;font-size:12.5px;color:#aab3c0;text-align:right;flex:0 0 auto}
  .zone.filled .zone-status{color:#8fbf9f}
  input[type=file]{display:none}
  button{font:inherit;font-weight:600;background:#e3935f;color:#1c1a16;border:none;border-radius:6px;
         padding:12px 22px;cursor:pointer;margin-top:8px}
  button:disabled{opacity:.5;cursor:not-allowed}
  button.secondary{background:transparent;color:#c7bda6;border:1px solid #3a3428}
  pre{background:#242019;border:1px solid #3a3428;border-radius:6px;padding:14px;font-size:12.5px;
      white-space:pre-wrap;word-break:break-word;max-height:420px;overflow:auto;margin-top:20px}
  .row{display:flex;gap:10px;align-items:center}
  .ok{color:#8fbf9f}.bad{color:#e0796b}
  .hint{font-size:12.5px;color:#aab3c0;margin-top:6px}
</style></head>
<body>
  <h1>Build today's desk</h1>
  <p class="lede">Drop the five export files below, then click Build. This runs <code>make plan &amp; make content &amp; make site</code> to generate your desk from fresh data.</p>

  <div id="zones"></div>

  <div class="row">
    <button id="buildBtn" disabled>Build the desk</button>
    <button id="serveBtn" class="secondary" style="display:none">Open the built page</button>
  </div>

  <pre id="log" style="display:none"></pre>

<script>
const TARGETS = __TARGETS__;
const zones = document.getElementById('zones');
const files = {};

TARGETS.forEach(([suffix, dest, label]) => {
  const z = document.createElement('div');
  z.className = 'zone';
  z.innerHTML = `
    <div>
      <div class="zone-label">${label}</div>
      <div class="zone-sub">drop the CSV here, or click to browse</div>
    </div>
    <div class="zone-status">not added</div>
    <input type="file" accept=".csv" />`;
  const input = z.querySelector('input');
  const status = z.querySelector('.zone-status');

  function take(file) {
    if (!file) return;
    files[suffix] = file;
    z.classList.add('filled');
    status.textContent = file.name;
    updateButton();
  }
  z.addEventListener('click', () => input.click());
  input.addEventListener('change', e => take(e.target.files[0]));
  z.addEventListener('dragover', e => { e.preventDefault(); z.classList.add('drag'); });
  z.addEventListener('dragleave', () => z.classList.remove('drag'));
  z.addEventListener('drop', e => {
    e.preventDefault(); z.classList.remove('drag');
    take(e.dataTransfer.files[0]);
  });
  zones.appendChild(z);
});

function updateButton() {
  document.getElementById('buildBtn').disabled = Object.keys(files).length !== TARGETS.length;
}

document.getElementById('buildBtn').addEventListener('click', async () => {
  const btn = document.getElementById('buildBtn');
  const log = document.getElementById('log');
  btn.disabled = true; btn.textContent = 'Building...';
  log.style.display = 'block'; log.textContent = 'Uploading files & building pipeline...';

  const fd = new FormData();
  Object.values(files).forEach(f => fd.append('files', f, f.name));

  try {
    const res = await fetch('/build', { method: 'POST', body: fd });
    const data = await res.json();
    log.textContent = data.log;
    if (data.ok) {
      log.classList.add('ok');
      document.getElementById('serveBtn').style.display = 'inline-block';
      btn.textContent = 'Build the desk again';
    } else {
      log.classList.add('bad');
      btn.textContent = 'Build failed -- see log';
    }
  } catch (err) {
    log.textContent = 'Request failed: ' + err;
    btn.textContent = 'Try again';
  }
  btn.disabled = false;
});

document.getElementById('serveBtn').addEventListener('click', () => {
  window.location.href = '/desk';
});
</script>
</body></html>"""


def parse_multipart(body, boundary):
    parts = body.split(b'--' + boundary)
    out = []
    for part in parts:
        part = part.strip(b'\r\n')
        if not part or part == b'--':
            continue
        header_end = part.find(b'\r\n\r\n')
        if header_end == -1:
            continue
        headers = part[:header_end].decode('utf-8', 'replace')
        data = part[header_end + 4:]
        if data.endswith(b'\r\n'):
            data = data[:-2]
        m = re.search(r'filename="([^"]*)"', headers)
        if not m or not m.group(1):
            continue
        out.append((m.group(1), data))
    return out


def run_step(cmd, env):
    proc = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True)
    tag = f"$ {' '.join(cmd)}\n"
    out = tag + proc.stdout + proc.stderr
    return proc.returncode == 0, out


ACCESS_KEY = os.environ.get('HUSTAD_ACCESS_KEY', 'hustad2026')

LOGIN_PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Hustad System — Authorized Login</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Outfit:wght@600;700&display=swap">
<style>
:root { --paper: #0B0F17; --card: #131924; --copper: #E5A93B; --ink: #F3F4F6; --ink-2: #9CA3AF; --line: rgba(255,255,255,0.08); }
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: "Plus Jakarta Sans", sans-serif; background: var(--paper); color: var(--ink); display: flex; align-items: center; justify-content: center; min-height: 100vh; background-image: radial-gradient(ellipse at 50% 0%, rgba(229,169,59,0.12) 0%, transparent 70%); }
.card { background: var(--card); border: 1px solid var(--line); border-radius: 16px; padding: 40px; width: 100%; max-width: 420px; box-shadow: 0 20px 50px rgba(0,0,0,0.5); text-align: center; }
.logo { font-family: Outfit, sans-serif; font-size: 12px; font-weight: 700; letter-spacing: .25em; color: var(--copper); text-transform: uppercase; margin-bottom: 8px; }
h1 { font-family: Outfit, sans-serif; font-size: 24px; font-weight: 700; margin-bottom: 8px; }
p { font-size: 14px; color: var(--ink-2); margin-bottom: 28px; }
form { display: flex; flex-direction: column; gap: 16px; }
input { font-family: inherit; font-size: 16px; padding: 14px 16px; background: rgba(255,255,255,0.04); border: 1px solid var(--line); border-radius: 10px; color: var(--ink); outline: none; transition: all 0.2s ease; text-align: center; letter-spacing: 2px; }
input:focus { border-color: var(--copper); box-shadow: 0 0 0 3px rgba(229,169,59,0.15); }
button { font-family: inherit; font-size: 13px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; padding: 14px; background: linear-gradient(135deg, #E5A93B, #D48828); color: #0F141E; border: 0; border-radius: 10px; cursor: pointer; transition: all 0.2s ease; box-shadow: 0 4px 16px rgba(229,169,59,0.25); }
button:hover { transform: translateY(-1px); box-shadow: 0 6px 20px rgba(229,169,59,0.35); }
.err { color: #EF4444; font-size: 13px; margin-top: 14px; }
</style>
</head>
<body>
<div class="card">
  <div class="logo">HUSTAD COMPANIES</div>
  <h1>Authorized Access</h1>
  <p>Enter system passcode to access the LinkedIn Outreach & Content Desk.</p>
  <form method="POST" action="/login">
    <input type="password" name="passcode" placeholder="••••••••" required autofocus>
    <button type="submit">Sign In to Desk</button>
  </form>
  __ERR__
</div>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def check_auth(self):
        cookie = self.headers.get('Cookie', '')
        return 'hustad_session=authenticated' in cookie

    def do_GET(self):
        if self.path == '/logout':
            self.send_response(302)
            self.send_header('Set-Cookie', 'hustad_session=; Path=/; Max-Age=0')
            self.send_header('Location', '/login')
            self.end_headers()
            return

        if self.path == '/login':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(LOGIN_PAGE.replace('__ERR__', '').encode('utf-8'))
            return

        if not self.check_auth() and not self.path.startswith('/api/webhook'):
            self.send_response(302)
            self.send_header('Location', '/login')
            self.end_headers()
            return

        if self.path.startswith('/api/desk'):
            import api
            import json
            data = api.get_desk_data()
            body = json.dumps(data).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if self.path.startswith('/api/validate_csv'):
            import sanitize
            import json
            data = sanitize.validate_raw_exports()
            body = json.dumps(data).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if self.path.startswith('/api/sync_crm'):
            import crm_sync
            import json
            data = crm_sync.export_crm_payload()
            body = json.dumps(data).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if self.path.startswith('/api/friday_report'):
            import friday_review
            import json
            data = friday_review.generate_friday_report()
            body = json.dumps(data).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if self.path.startswith('/api/health'):
            import json
            res = subprocess.run(['python3', 'scripts/check_invariants.py'], cwd=ROOT, capture_output=True, text=True)
            data = {'ok': res.returncode == 0, 'status': 'PASS' if res.returncode == 0 else 'FAIL', 'output': res.stdout}
            body = json.dumps(data).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if self.path.startswith('/api/digest'):
            sys.path.insert(0, os.path.join(ROOT, 'scripts'))
            import email_digest
            body = email_digest.generate_weekly_digest_html().encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if self.path.startswith('/api/workbook'):
            wb_path = os.path.join(ROOT, 'data', 'out', 'master_workbook.xlsx')
            if not os.path.exists(wb_path):
                subprocess.run(['make', 'workbook'], cwd=ROOT)
            if os.path.exists(wb_path):
                self.send_response(200)
                self.send_header('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                self.send_header('Content-Disposition', 'attachment; filename="master_workbook.xlsx"')
                with open(wb_path, 'rb') as f:
                    data = f.read()
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            else:
                self.send_response(404)
                self.end_headers()
            return

        if self.path.startswith('/api/stats'):
            import api
            import json
            data = api.get_analytics_data()
            body = json.dumps(data).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if self.path in ('/desk', '/preview', '/preview.html'):
            site = os.path.join(ROOT, 'site', 'index.html')
            if os.path.exists(site):
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers()
                with open(site, 'rb') as f:
                    content = f.read().decode('utf-8', 'replace')
                banner = '<div style="background:#242019;color:#efe8d8;padding:8px 16px;font-family:sans-serif;font-size:13px;display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #3a3428;"><span>Hustad LinkedIn Desk</span><a href="/upload" style="color:#e3935f;text-decoration:none;font-weight:600;">📤 Upload New CSV Data</a></div>'
                if '<body>' in content:
                    content = content.replace('<body>', '<body>' + banner, 1)
                self.wfile.write(content.encode('utf-8'))
                return
            else:
                self.send_response(302)
                self.send_header('Location', '/upload')
                self.end_headers()
                return

        site = os.path.join(ROOT, 'site', 'index.html')
        if self.path == '/' and os.path.exists(site):
            self.send_response(302)
            self.send_header('Location', '/desk')
            self.end_headers()
            return

        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        targets_json = str([[s, d, html.escape(l)] for s, d, l in RAW_TARGETS]).replace("'", '"')
        self.wfile.write(PAGE.replace('__TARGETS__', targets_json).encode('utf-8'))

    def do_POST(self):
        if self.path == '/login':
            import urllib.parse
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length).decode('utf-8', 'ignore')
            params = urllib.parse.parse_qs(body)
            submitted_pass = params.get('passcode', [''])[0]
            if submitted_pass == ACCESS_KEY:
                self.send_response(302)
                self.send_header('Set-Cookie', 'hustad_session=authenticated; Path=/; HttpOnly; SameSite=Lax')
                self.send_header('Location', '/desk')
                self.end_headers()
                return
            else:
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers()
                err_msg = '<p class="err">Invalid passcode. Please try again.</p>'
                self.wfile.write(LOGIN_PAGE.replace('__ERR__', err_msg).encode('utf-8'))
                return

        if self.path.startswith('/api/webhook/graph'):
            import ingest_replies
            import json
            # Handle Microsoft Graph subscription validation
            if 'validationToken=' in self.path:
                token = self.path.split('validationToken=')[1].split('&')[0]
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                self.wfile.write(token.encode('utf-8'))
                return

            length = int(self.headers.get('Content-Length', 0))
            payload = json.loads(self.rfile.read(length).decode('utf-8') or '{}')
            value = payload.get('value', [{}])[0]
            resource_data = value.get('resourceData', {})
            
            res = ingest_replies.ingest_reply(
                sender_email=resource_data.get('sender', {}).get('emailAddress', {}).get('address', ''),
                sender_name=resource_data.get('sender', {}).get('emailAddress', {}).get('name', ''),
                message_body=resource_data.get('bodyPreview', '')
            )
            body = json.dumps(res).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if self.path.startswith('/api/ingest_replies'):
            import ingest_replies
            import json
            length = int(self.headers.get('Content-Length', 0))
            payload = json.loads(self.rfile.read(length).decode('utf-8') or '{}')
            res = ingest_replies.ingest_reply(
                sender_email=payload.get('email', ''),
                sender_name=payload.get('name', ''),
                message_body=payload.get('body', '')
            )
            body = json.dumps(res).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if self.path != '/build':
            self.send_response(404)
            self.end_headers()
            return
        ctype = self.headers.get('Content-Type', '')
        m = re.search(r'boundary=(.+)', ctype)
        if not m:
            self.send_response(400)
            self.end_headers()
            return
        boundary = m.group(1).strip().encode()
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)
        uploads = parse_multipart(body, boundary)

        subprocess.run(['rm', '-rf', 'data/raw', 'data/work', 'data/research', 'site/index.html'], cwd=ROOT)
        os.makedirs(paths.s(paths.RAW), exist_ok=True)

        log_lines = []
        matched = set()
        for filename, data in uploads:
            dest, label = target_for(filename)
            if not dest:
                log_lines.append(f"skipped {filename}: didn't recognize which export this is")
                continue
            with open(os.path.join(paths.s(paths.RAW), dest), 'wb') as f:
                f.write(data)
            matched.add(dest)
            log_lines.append(f"saved {filename} -> data/raw/{dest} ({label})")

        missing = [dest for _, dest, label in RAW_TARGETS if dest not in matched]
        if missing:
            log_lines.append('')
            log_lines.append('Stopped: missing ' + ', '.join(missing))
            self._reply(False, '\n'.join(log_lines))
            return

        env = os.environ.copy()
        ok = True
        for step in (['make', 'plan'], ['make', 'content'], ['make', 'site']):
            log_lines.append('')
            success, out = run_step(step, env)
            log_lines.append(out.strip())
            if not success:
                ok = False
                break

        if ok:
            log_lines.append('\nBuilt site/index.html cleanly. Click "Open the built page" to view your desk!')
        self._reply(ok, '\n'.join(log_lines))

    def _reply(self, ok, log):
        import json
        body = json.dumps({'ok': ok, 'log': log}).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    server = ThreadingHTTPServer(('0.0.0.0', PORT), Handler)
    url = f'http://0.0.0.0:{PORT}'
    print(f'Serving the application at {url}')
    if 'PORT' not in os.environ:
        threading.Timer(0.6, lambda: webbrowser.open(f'http://127.0.0.1:{PORT}')).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
