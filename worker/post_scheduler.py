#!/usr/bin/env python3
"""
The posting worker: publishes the day's due calendar posts to LinkedIn through the official API.

This is the ONLY component in the system that touches LinkedIn, and it touches exactly one
surface: creating posts. It will never send, read, or automate a direct message. That is a
platform rule (there is no public DM API) and a program rule (docs/PRIVACY.md, README rule 2),
and this worker asserts it structurally: it consumes content_calendar.json, which cannot
contain a DM by construction.

What it automates, per format:
  text      fully automated: POST /rest/posts with the commentary
  graphic   automated when data/out/assets/<id>.png exists (see render_assets.py):
            initializeUpload on /rest/images, PUT the binary, reference the URN in the post
  carousel  automated when data/out/assets/<id>.pdf exists:
            initializeUpload on /rest/documents, PUT the PDF, reference the URN
Newsletters and articles are NOT here: LinkedIn has no API for either. They stay ten minute
manual publishes from the Newsletter and Articles tabs.

Environment:
  LINKEDIN_ACCESS_TOKEN   required to go live. 60 day member token; see docs/API_INTEGRATIONS.md
  LINKEDIN_AUTHOR_URN     urn:li:person:XXXX for Eric's posts (from /v2/userinfo sub claim)
  LINKEDIN_ORG_URN        urn:li:organization:XXXX; only used for channel=company posts, and only
                          once the Community Management API application is approved
  LINKEDIN_VERSION        Linkedin-Version header, YYYYMM. Default 202605. Rotate quarterly.
  DRY_RUN                 default 1. Prints every payload and posts nothing. Set 0 to go live.

State: worker/state/posted.json maps post id -> {at, urn}. A post already in the state file is
never posted again, so reruns and overlapping cron fires are safe. The GitHub workflow commits
this file back after a live run.

Run it:  python3 worker/post_scheduler.py [--date 2026-09-01] [--force-id C-0901]
"""
import sys, os, json, datetime, urllib.request, urllib.error
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'pipeline'))
import paths

API = 'https://api.linkedin.com'
STATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'state', 'posted.json')
ASSETS = paths.s(paths.OUT / 'assets')

DRY = os.environ.get('DRY_RUN', '1') != '0'
TOKEN = os.environ.get('LINKEDIN_ACCESS_TOKEN', '')
AUTHOR = os.environ.get('LINKEDIN_AUTHOR_URN', '')
ORG = os.environ.get('LINKEDIN_ORG_URN', '')
VERSION = os.environ.get('LINKEDIN_VERSION', '202605')

def arg(name, default=''):
    a = sys.argv[1:]
    return a[a.index(name) + 1] if name in a else default

def chicago_today():
    # zoneinfo, not a fixed offset: the calendar is written in Central time.
    from zoneinfo import ZoneInfo
    return datetime.datetime.now(ZoneInfo('America/Chicago')).date().isoformat()

def load_state():
    try: return json.load(open(STATE))
    except Exception: return {}

def save_state(st):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    json.dump(st, open(STATE, 'w'), indent=1, sort_keys=True)

class ApiError(RuntimeError):
    def __init__(self, status, detail):
        super().__init__(f'LinkedIn API {status}: {detail}')
        self.status = status

def req(method, url, body=None, raw=None, ctype='application/json', versioned=True):
    headers = {'Authorization': f'Bearer {TOKEN}', 'X-Restli-Protocol-Version': '2.0.0'}
    if versioned: headers['Linkedin-Version'] = VERSION
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    if data is not None: headers['Content-Type'] = ctype
    r = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(r, timeout=60) as resp:
            txt = resp.read()
            return resp.status, dict(resp.headers), (json.loads(txt) if txt.strip().startswith(b'{') else txt)
    except urllib.error.HTTPError as e:
        detail = e.read()[:300].decode('utf-8', 'replace')
        if e.code == 401:
            raise ApiError(401, 'token expired or invalid. Mint a new member token (60 day life, '
                                'docs/API_INTEGRATIONS.md, self serve section) and update the '
                                'LINKEDIN_ACCESS_TOKEN secret. Nothing was posted.') from None
        if e.code == 429:
            raise ApiError(429, 'rate limited. At four posts a week this means a loop; stop and '
                                'read worker/state/posted.json before retrying. ' + detail) from None
        raise ApiError(e.code, detail) from None

def upload_media(kind, path, owner):
    """kind: 'images' or 'documents'. Returns the media URN."""
    _, _, init = req('POST', f'{API}/rest/{kind}?action=initializeUpload',
                     body={'initializeUploadRequest': {'owner': owner}})
    up = init['value']
    with open(path, 'rb') as f:
        blob = f.read()
    ctype = 'application/pdf' if path.endswith('.pdf') else 'image/png'
    status, _, _ = req('PUT', up['uploadUrl'], raw=blob, ctype=ctype, versioned=False)
    if status >= 300:
        raise RuntimeError(f'upload failed with {status} for {path}')
    return up.get('image') or up.get('document')

def commentary(p):
    parts = [p['hook']] + p.get('body', [])
    if p.get('cta'): parts.append(p['cta'])
    if p.get('hashtags'): parts.append(' '.join('#' + t for t in p['hashtags']))
    return '\n\n'.join(parts)

def payload(p, media_urn=None, media_title=''):
    author = ORG if p.get('channel') == 'company' else AUTHOR
    body = {
      'author': author,
      'commentary': commentary(p),
      'visibility': 'PUBLIC',
      'distribution': {'feedDistribution': 'MAIN_FEED', 'targetEntities': [], 'thirdPartyDistributionChannels': []},
      'lifecycleState': 'PUBLISHED',
      'isReshareDisabledByAuthor': False,
    }
    if media_urn:
        body['content'] = {'media': {'id': media_urn, 'title': media_title}}
    return body

def main():
    cal_path = paths.WORK / 'content_calendar.json'
    if not cal_path.exists():
        print('no content calendar; run: python3 pipeline/content_engine.py'); return 1
    cal = json.load(open(cal_path))
    day = arg('--date') or chicago_today()
    force = arg('--force-id')
    state = load_state()
    due = [p for p in cal['posts'] if (p['id'] == force) or (not force and p['date'] == day)]
    if not due:
        print(f'{day}: nothing scheduled'); return 0
    posted = 0
    for p in due:
        if p['id'] in state and not force:
            print(f"{p['id']}: already posted at {state[p['id']]['at']}, skipping"); continue
        if p['channel'] == 'company' and not ORG:
            print(f"{p['id']}: company post, LINKEDIN_ORG_URN not set (Community Management API "
                  'not approved yet?). Post it by hand from the Posts tab today.'); continue
        author = ORG if p['channel'] == 'company' else AUTHOR
        media, mtitle = None, ''
        if p['format'] == 'photo':
            print(f"{p['id']}: real photo post; the photo is chosen and attached by hand from the "
                  'Posts tab, per the content standards. Not automated on purpose.'); continue
        if p['format'] == 'graphic':
            f = os.path.join(ASSETS, f"{p['id']}.png")
            if not os.path.exists(f):
                print(f"{p['id']}: graphic post but {f} missing. Run worker/render_assets.py first. "
                      'Skipping; post by hand from the tab.'); continue
            media, mtitle = ('images', f), p.get('theme', 'Hustad')
        elif p['format'] == 'carousel':
            f = os.path.join(ASSETS, f"{p['id']}.pdf")
            if not os.path.exists(f):
                print(f"{p['id']}: carousel post but {f} missing. Run worker/render_assets.py first. "
                      'Skipping; post by hand from the tab.'); continue
            media, mtitle = ('documents', f), (p.get('asset', {}).get('title') or 'Hustad')
        if DRY:
            print(f"DRY {p['id']} [{p['channel']}/{p['format']}] author={author or '(unset)'}")
            print(json.dumps(payload(p, 'urn:li:PREVIEW' if media else None, mtitle), indent=1)[:600])
            continue
        if not TOKEN or not author:
            print(f"{p['id']}: LINKEDIN_ACCESS_TOKEN / author URN not set; cannot go live"); return 1
        urn = None
        if media:
            try:
                urn = upload_media(media[0], media[1], author)
            except ApiError as e:
                print(f"{p['id']}: media upload failed, {e}"); return 1
        try:
            status, headers, _ = req('POST', f'{API}/rest/posts', body=payload(p, urn, mtitle))
        except ApiError as e:
            print(f"{p['id']}: {e}")
            return 1 if e.status in (401, 429) else 1
        if status in (200, 201):
            post_urn = headers.get('x-restli-id', '')
            state[p['id']] = {'at': datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),
                              'urn': post_urn}
            save_state(state)
            posted += 1
            print(f"{p['id']}: published, {post_urn}")
        else:
            print(f"{p['id']}: unexpected status {status}"); return 1
    print(f'{day}: {posted} published, dry_run={DRY}')
    return 0

if __name__ == '__main__':
    sys.exit(main())
