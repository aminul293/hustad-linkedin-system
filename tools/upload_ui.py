"""
A tiny local web page so building the desk doesn't require a terminal or a file browser.

Drag in the five export files, click Build, and this runs the same `make plan && make content &&
make site` sequence the README already documents -- just triggered by a click instead of three
typed commands. Nothing here talks to the internet: it is a stdlib-only HTTP server bound to
localhost, meant to run on whichever machine already has the raw exports on it.

Start it with `make upload` (see the Makefile). It opens http://localhost:8765 automatically.

Why this exists instead of a real upload form on a hosted page: the raw files are a LinkedIn
connections export and a CRM opportunity export -- exactly the data docs/PRIVACY.md says must
never leave a controlled machine or pass through a third party. A page anyone could reach over the
internet is the wrong shape for that. This is a local tool, not a hosted service, on purpose.
"""
import sys, os, subprocess, threading, webbrowser, html, re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import paths  # noqa: E402

PORT = int(os.environ.get('HUSTAD_UPLOAD_PORT', '8765'))

# Suffix a dropped file is matched against -> exact filename the pipeline scripts already expect
# on disk (see pipeline/classify.py and pipeline/active_accounts.py). Renaming on save means the
# pipeline code itself never has to change, and a fresh LinkedIn export -- which always ships with
# a different random ID prefix -- still lands in the right place.
RAW_TARGETS = [
    ('Connections.csv',              'a6350e6d-Connections.csv',            'LinkedIn connections export'),
    ('Invitations.csv',              'ff13996e-Invitations.csv',            'LinkedIn invitations export'),
    ('messages.csv',                 '86563516-messages.csv',               'LinkedIn messages export'),
    ('Endorsement_Received_Info.csv', '3da803c8-Endorsement_Received_Info.csv', 'LinkedIn endorsements export'),
    ('opportunities',                'opportunities_2026.csv',              'CRM opportunity export'),
]

def target_for(filename):
    """Match an uploaded filename to the slot it fills, by suffix (or, for the CRM file, by a
    looser 'contains' match since that export's name isn't LinkedIn-fixed)."""
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
  <p class="lede">Drop the five export files below, then click Build. This runs the same steps as
  <code>make plan &amp; make content &amp; make site</code> and tells you when it's done.</p>

  <div id="zones"></div>

  <div class="row">
    <button id="buildBtn" disabled>Build the desk</button>
    <button id="serveBtn" class="secondary" style="display:none">Open the built page</button>
  </div>
  <div class="hint">Nothing here leaves this computer -- see tools/upload_ui.py for why.</div>

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
  log.style.display = 'block'; log.textContent = 'Uploading files...';

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
  window.open('/preview', '_blank');
});
</script>
</body></html>"""


def parse_multipart(body, boundary):
    """Minimal multipart/form-data parser for file fields only -- no dependency on the stdlib
    `cgi` module, which is gone as of Python 3.13. Good enough for a handful of CSV uploads to a
    tool that only ever talks to itself on localhost."""
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


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass  # keep the terminal quiet; the log goes to the browser instead

    def do_GET(self):
        if self.path == '/preview':
            site = os.path.join(ROOT, 'site', 'index.html')
            if os.path.exists(site):
                self.send_response(302)
                self.send_header('Location', '/preview.html')
                self.end_headers()
            else:
                self.send_response(404)
                self.end_headers()
            return
        if self.path == '/preview.html':
            site = os.path.join(ROOT, 'site', 'index.html')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            with open(site, 'rb') as f:
                self.wfile.write(f.read())
            return
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        targets_json = str([[s, d, html.escape(l)] for s, d, l in RAW_TARGETS]).replace("'", '"')
        self.wfile.write(PAGE.replace('__TARGETS__', targets_json).encode('utf-8'))

    def do_POST(self):
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

        log_lines = []
        os.makedirs(paths.s(paths.RAW), exist_ok=True)
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
            log_lines.append('\nBuilt site/index.html. Click "Open the built page" to look at it.')
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
    server = ThreadingHTTPServer(('127.0.0.1', PORT), Handler)
    url = f'http://127.0.0.1:{PORT}'
    print(f'Serving the upload page at {url}')
    threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
