# -*- coding: utf-8 -*-
"""
The studio: server-side rendering for the Replies, Posts, Newsletter and Articles panes of the
Command Center page, plus the SVG asset templates for post graphics and carousel slides.

Everything here returns strings that build_desk.py splices into the one page. No client-side
templating: the page ships rendered, and the JS only wires state (posted ticks, statuses, copy
buttons, PNG export, carousel print).

The graphics are deliberately self-contained SVG with a system font stack, because the PNG export
path serializes the SVG into a canvas, where webfonts do not travel. Brand tokens live in BRAND;
swapping these five values re-skins every asset.
"""
import html, json, textwrap

# The house design system from docs/CONTENT_STANDARDS.md Part 4: deep slate ground, warm white
# text, a single sand accent, Lora serif display with Poppins body, hairline footer, 4:5 formats.
# Swap the hex values here if the brand guide revises them; everything follows.
BRAND = {
  'ground':  '#152438',   # deep slate, the card ground
  'paper':   '#F4EFE6',   # warm white, primary text on ground
  'muted':   '#9FB0C4',   # secondary text on ground
  'accent':  '#CDA672',   # the single sand accent
}
# Lora and Poppins load on the page and in the CI renderer; the fallbacks keep the geometry sane
# anywhere the webfonts cannot travel (the in-page canvas PNG export).
FONT_DISPLAY = "Lora, Georgia, 'Times New Roman', serif"
FONT_BODY = "Poppins, 'Helvetica Neue', Arial, sans-serif" 

def esc(s):
    return html.escape(str(s if s is not None else ''), quote=True)

def jsafe(v):
    """JSON for embedding in a <script> block: '</' must not close the tag."""
    return json.dumps(v, ensure_ascii=False).replace('</', '<' + chr(92) + '/')

def _wrap(s, width):
    return textwrap.wrap(str(s), width=width, break_long_words=False) or ['']

def _tspans(lines, x, y, lh):
    out = []
    for i, ln in enumerate(lines):
        out.append(f'<tspan x="{x}" y="{y + i * lh}">{esc(ln)}</tspan>')
    return ''.join(out)

def _frame(w, h, inner):
    """Deep slate ground, hairline footer rule, small wordmark. The house frame."""
    b = BRAND
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
            f'font-family="{FONT_BODY}">'
            f'<rect width="{w}" height="{h}" fill="{b["ground"]}"/>'
            f'<rect x="72" y="{h-96}" width="{w-144}" height="2" fill="{b["accent"]}" opacity="0.55"/>'
            f'<text x="72" y="{h-40}" font-size="24" font-weight="600" letter-spacing="7" fill="{b["paper"]}" opacity="0.85">HUSTAD</text>'
            + inner + '</svg>')

def svg_stat(a):
    """1200 x 1500 stat card: kicker, one large serif figure, unit, support line, source."""
    b = BRAND; w, h = 1200, 1500
    stat = str(a.get('stat', ''))
    size = 160 if len(stat) <= 10 else (120 if len(stat) <= 15 else 92)
    unit_l = _wrap(a.get('unit', ''), 36)
    line_l = _wrap(a.get('line', ''), 40)
    y = 560
    inner = (
      f'<rect x="72" y="120" width="88" height="8" fill="{b["accent"]}"/>'
      f'<text x="72" y="200" font-size="32" font-weight="600" letter-spacing="5" fill="{b["accent"]}">{esc(a.get("kicker",""))}</text>'
      f'<text x="72" y="{y}" font-family="{FONT_DISPLAY}" font-size="{size}" font-weight="600" fill="{b["paper"]}">{esc(stat)}</text>'
      f'<text font-size="42" font-weight="400" fill="{b["muted"]}">{_tspans(unit_l, 72, y+96, 58)}</text>'
      f'<text font-size="38" fill="{b["paper"]}">{_tspans(line_l, 72, y+96+len(unit_l)*58+80, 56)}</text>'
      f'<text x="72" y="{h-140}" font-size="26" fill="{b["muted"]}">{esc(a.get("source",""))}</text>')
    return _frame(w, h, inner)

def svg_check(a):
    """1200 x 1500 checklist card: kicker, serif title, items marked by a short sand rule.
    No icon glyphs, per the house system."""
    b = BRAND; w, h = 1200, 1500
    title_l = _wrap(a.get('title', ''), 24)
    inner = [
      f'<rect x="72" y="120" width="88" height="8" fill="{b["accent"]}"/>',
      f'<text x="72" y="200" font-size="32" font-weight="600" letter-spacing="5" fill="{b["accent"]}">{esc(a.get("kicker",""))}</text>',
      f'<text font-family="{FONT_DISPLAY}" font-size="70" font-weight="600" fill="{b["paper"]}">{_tspans(title_l, 72, 320, 88)}</text>']
    y = 320 + len(title_l) * 88 + 64
    for it in a.get('items', []):
        lines = _wrap(it, 38)
        inner.append(f'<rect x="72" y="{y-14}" width="30" height="4" fill="{b["accent"]}"/>')
        inner.append(f'<text font-size="38" fill="{b["paper"]}">{_tspans(lines, 134, y, 54)}</text>')
        y += len(lines) * 54 + 42
    if a.get('source'):
        inner.append(f'<text x="72" y="{h-140}" font-size="26" fill="{b["muted"]}">{esc(a["source"])}</text>')
    return _frame(w, h, ''.join(inner))

def svg_slides(a):
    """Carousel: 1080 x 1350 cover plus one slide per item, serif display over Poppins body,
    one idea per slide. Returns a list of SVG strings."""
    b = BRAND; w, h = 1080, 1350
    slides = a.get('slides', [])
    out = []
    title_l = _wrap(a.get('title', ''), 17)
    sub_l = _wrap(a.get('subtitle', ''), 31)
    cover = (
      f'<rect x="72" y="150" width="88" height="8" fill="{b["accent"]}"/>'
      f'<text font-family="{FONT_DISPLAY}" font-size="90" font-weight="600" fill="{b["paper"]}">{_tspans(title_l, 72, 340, 108)}</text>'
      f'<text font-size="42" fill="{b["muted"]}">{_tspans(sub_l, 72, 340+len(title_l)*108+70, 58)}</text>'
      f'<text x="72" y="{h-160}" font-size="32" fill="{b["accent"]}" font-weight="600">Swipe &#8594;</text>')
    out.append(_frame(w, h, cover))
    n = len(slides)
    for i, s in enumerate(slides, 1):
        h_l = _wrap(s.get('h', ''), 21)
        b_l = _wrap(s.get('b', ''), 37)
        last = (i == n)
        num = (f'<text x="72" y="230" font-family="{FONT_DISPLAY}" font-size="112" font-weight="600" '
               f'fill="{b["accent"]}">{i:02d}</text>') if not last else \
              (f'<rect x="72" y="150" width="88" height="8" fill="{b["accent"]}"/>')
        body_y = 330 + len(h_l) * 76 + 60
        inner = (num
          + f'<text font-family="{FONT_DISPLAY}" font-size="58" font-weight="600" fill="{b["paper"]}">{_tspans(h_l, 72, 330 if not last else 300, 76)}</text>'
          + f'<text font-size="38" fill="{b["muted"]}">{_tspans(b_l, 72, body_y, 56)}</text>'
          + f'<text x="{w-72}" y="{h-40}" text-anchor="end" font-size="24" fill="{b["muted"]}">{i+1} / {n+1}</text>')
        out.append(_frame(w, h, inner))
    return out

# ---------------------------------------------------------------------------
# Copy text assembly: what the Copy button puts on the clipboard for a post.
# ---------------------------------------------------------------------------
def post_copy_text(p):
    parts = [p['hook']] + p.get('body', [])
    if p.get('cta'): parts.append(p['cta'])
    if p.get('hashtags'): parts.append(' '.join('#' + t for t in p['hashtags']))
    return '\n\n'.join(parts)

def _chip(label, cls=''):
    return f'<span class="chip {cls}">{esc(label)}</span>'

def render_post(p):
    fmt = p.get('format', 'text')
    ch = p.get('channel', 'personal')
    chips = (_chip(p.get('dow', '') + ' ' + p['date'], 'chip-id')
             + _chip('Company page' if ch == 'company' else 'Personal', 'chip-ch-' + ch)
             + _chip({'text': 'Text', 'graphic': 'Graphic', 'carousel': 'Carousel PDF', 'photo': 'Text + real photo'}.get(fmt, 'Text'))
             + _chip(p.get('time', ''), '') + _chip(p.get('theme', '')))
    asset_html = ''
    if fmt == 'photo':
        asset_html = ('<div class="check"><p><span class="lbl">The photo, before it attaches</span>'
          'One real field photo, chosen from the archive or the week. No client or property '
          'identifiers, no doctored edits (brightness, contrast and crop only), crew visibly tied '
          'off if anyone is on a roof. If nothing clears that bar, the text runs alone and that is fine.</p></div>')
    a = p.get('asset')
    if a and a.get('template') in ('stat', 'check'):
        svg = svg_stat(a) if a['template'] == 'stat' else svg_check(a)
        asset_html = ('<div class="asset"><div class="asset-fr">' + svg + '</div>'
          + '<div class="asset-side"><p class="hint">Attach this card as the post image. '
          + 'Download PNG here is a quick export with system fonts; the feed-final Lora and Poppins '
          + 'render comes from make assets (or the deployed pipeline). SVG is the editable source.</p>'
          + f'<div class="btns"><button class="btn dlpng" type="button" data-name="{esc(p["id"])}.png">Download PNG</button>'
          + f'<button class="btn ghost dlsvg" type="button" data-name="{esc(p["id"])}.svg">Download SVG</button></div></div></div>')
    elif a and a.get('template') == 'carousel':
        slides = svg_slides(a)
        strip = ''.join(f'<div class="slide">{s}</div>' for s in slides)
        asset_html = ('<div class="asset"><div class="slides">' + strip + '</div>'
          + '<div class="asset-side"><p class="hint">Post this as a document so it swipes: '
          + 'Print slides opens a print view with one slide per page; choose Save as PDF, then '
          + 'upload the PDF to the post. ' + str(len(slides)) + ' pages.</p>'
          + f'<div class="btns"><button class="btn prslides" type="button">Print slides to PDF</button></div></div></div>')
    fact = ''
    if p.get('fact_detail'):
        fd = p['fact_detail']
        fact = ('<p class="factline"><span class="lbl">Claim on the card, verified</span>'
                + esc(fd['claim']) + ' <i>' + esc(fd['source']) + '</i></p>')
    tags = ' '.join('#' + t for t in p.get('hashtags', []))
    body = ''.join(f'<p>{esc(x)}</p>' for x in p.get('body', []))
    cta = f'<p class="cta">{esc(p["cta"])}</p>' if p.get('cta') else ''
    note = f'<p class="hint">{esc(p["notes"])}</p>' if p.get('notes') else ''
    return (f'<article class="row post" data-cid="{esc(p["id"])}">'
      + '<header class="row-head"><div class="who">'
      + f'<h2>{esc(p["hook"])}</h2></div>'
      + '<div class="marks"><label class="done"><input type="checkbox" class="cchk"><span>Posted</span></label></div></header>'
      + f'<div class="meta">{chips}</div>'
      + f'<div class="draft"><div class="draft-bar"><div class="tabs"><span class="tab is-on">Post text</span></div>'
      + f'<button class="copy ccopy" type="button">Copy</button></div>'
      + f'<div class="msg postbody">{body}{cta}<p class="tagline">{esc(tags)}</p></div></div>'
      + asset_html + fact + note
      + '<div class="note-row"><label><span class="lbl">Note / live URL after posting</span>'
      + '<input type="text" class="cnote" placeholder="paste the post URL here once it is up"></label></div>'
      + f'<script type="application/json" class="ctext">{jsafe(post_copy_text(p))}</script>'
      + '</article>')

def render_posts_pane(cal):
    posts = cal.get('posts', [])
    if not posts:
        return '<div class="empty">No content calendar yet. Run <b>make content</b> and rebuild.</div>'
    weeks = {}
    import datetime as _dt
    for p in posts:
        d = _dt.date(*map(int, p['date'].split('-')))
        key = d.isocalendar()[:2]
        weeks.setdefault(key, {'label': f'Week of {(d - _dt.timedelta(days=d.weekday())):%b %d}', 'items': []})
        weeks[key]['items'].append(p)
    out = ['<section class="panel"><h3>The posting week</h3>'
           '<p>Four slots: Tuesday a personal point of view, Wednesday the designed asset, '
           'Thursday the long companion tied to the month&rsquo;s newsletter or article, Saturday the human one. '
           'Carousels go out on the personal profile and the company page reshares them; the stat and checklist '
           'cards run on the company page and Eric reshares those. Copy the text, download or print the asset, '
           'post at the time on the chip, tick Posted, paste the live URL. Links go in the first comment, never the body.</p>'
           '<p><span class="lbl">The fifteen minutes around a post</span>'
           'Ten minutes before: comment on three to five posts from operators and facilities people, so the '
           'algorithm sees a participant, not a broadcaster. The first ninety minutes after: answer every comment; '
           'early replies are what carry a post to second degree feeds. The DM desk and this calendar are one '
           'system: forty people a day open Eric&rsquo;s profile after a DM, and these posts are what they find there.</p></section>']
    for key in sorted(weeks):
        w = weeks[key]
        out.append(f'<h3 class="wk">{esc(w["label"])}</h3>')
        out.extend(render_post(p) for p in sorted(w['items'], key=lambda x: x['date']))
    return ''.join(out)

def render_newsletter_pane(cal):
    nl = cal.get('newsletter', {})
    if not nl:
        return '<div class="empty">No newsletter plan in the calendar.</div>'
    out = [f'<section class="panel"><h3>{esc(nl.get("name",""))}</h3>'
           f'<p>{esc(nl.get("description",""))}</p><p class="hint">{esc(nl.get("cadence",""))}</p>'
           '<div class="check"><p><span class="lbl">Issue day, ten minutes, in order</span>'
           'Open LinkedIn &rarr; Write article &rarr; select the newsletter &rarr; paste the draft below &rarr; '
           'set the title and subject &rarr; publish at 8:00 AM CT &rarr; then publish the Thursday companion post '
           'from the Posts tab and put the newsletter link in its first comment.</p></div></section>']
    for iss in nl.get('issues', []):
        stat = iss.get('status', 'outline')
        body = ''.join(f'<p>{esc(x)}</p>' for x in iss.get('draft', []))
        out.append(f'<article class="row post" data-cid="NL-{iss["n"]}">'
          + f'<header class="row-head"><div class="who"><h2>Issue {iss["n"]}: {esc(iss["title"])}</h2>'
          + f'<p class="role">Subject: {esc(iss.get("subject",""))}</p></div>'
          + '<div class="marks"><label class="done"><input type="checkbox" class="cchk"><span>Published</span></label></div></header>'
          + '<div class="meta">' + _chip(iss.get('date', ''), 'chip-id')
          + _chip('Full draft' if stat == 'ready' else 'Outline, write from thesis', 'chip-' + ('ok' if stat == 'ready' else 'warn')) + '</div>'
          + '<div class="draft"><div class="draft-bar"><div class="tabs"><span class="tab is-on">'
          + ('Draft' if stat == 'ready' else 'Committed outline') + '</span></div>'
          + '<button class="copy ccopy" type="button">Copy</button></div>'
          + f'<div class="msg postbody">{body}</div></div>'
          + '<div class="note-row"><label><span class="lbl">Live URL once published</span>'
          + '<input type="text" class="cnote" placeholder="paste the newsletter link here"></label></div>'
          + f'<script type="application/json" class="ctext">{jsafe(chr(10).join([iss["title"], ""] + iss.get("draft", [])))}</script>'
          + '</article>')
    return ''.join(out)

PITCH_TEMPLATE = """Subject: Contributor piece for {outlet}: {title}

Hi {editor_first},

I run national exterior and roofing programs for occupied portfolios as EVP at Hustad Companies, and I write a monthly operating newsletter for facilities and asset leaders.

I would like to contribute a piece for {outlet}: "{title}". The angle: {angle} It teaches a decision, names no clients, and sells nothing.

Happy to send the full draft or an outline, whichever your process prefers, and to work to your length and calendar. Recent writing and bio: {links}.

Thank you either way,
Eric Caturia
Executive Vice President, Hustad Companies"""

def render_articles_pane(cal):
    arts = cal.get('articles', [])
    cad = cal.get('article_cadence', [])
    rep = cal.get('repurpose', [])
    out = ['<section class="panel"><h3>The pitch week</h3><ol>'
           + ''.join(f'<li>{esc(x)}</li>' for x in cad) + '</ol>'
           + '<p class="hint">One outlet at a time per article. Original work only. Statuses here move with you and stay saved.</p></section>']
    out.append('<section class="panel"><h3>Repurposing, after each publication</h3><ol>'
           + ''.join(f'<li>{esc(x)}</li>' for x in rep) + '</ol></section>')
    out.append('<article class="row post" data-cid="PITCH-T">'
      + '<header class="row-head"><div class="who"><h2>The pitch template</h2>'
      + '<p class="role">Fill the braces from the row below it. Three pitches a Wednesday, maximum.</p></div></header>'
      + '<div class="draft"><div class="draft-bar"><div class="tabs"><span class="tab is-on">Template</span></div>'
      + '<button class="copy ccopy" type="button">Copy</button></div>'
      + f'<div class="msg postbody">{"".join(f"<p>{esc(x)}</p>" for x in PITCH_TEMPLATE.split(chr(10)+chr(10)))}</div></div>'
      + f'<script type="application/json" class="ctext">{jsafe(PITCH_TEMPLATE)}</script>'
      + '</article>')
    months = {}
    for a in arts:
        months.setdefault(a['month'], []).append(a)
    STATUSES = ['planned', 'draft', 'pitched', 'accepted', 'published', 'declined']
    for m in sorted(months):
        out.append(f'<h3 class="wk">{m}</h3>')
        for a in months[m]:
            opts = ''.join(f'<option value="{s}"{" selected" if s == a.get("status") else ""}>{s}</option>' for s in STATUSES)
            out.append(f'<article class="row post art" data-cid="{esc(a["id"])}">'
              + f'<header class="row-head"><div class="who"><h2>{esc(a["title"])}</h2>'
              + f'<p class="role">{esc(a["outlet"])} &middot; {esc(a["audience"])}</p></div>'
              + f'<div class="marks"><select class="cstat" aria-label="Status">{opts}</select></div></header>'
              + '<div class="meta">' + _chip(f'Tier {a["tier"]}') + _chip(a['month'], 'chip-id')
              + f'<a class="profile" href="{esc(a["route"])}" target="_blank" rel="noopener">{esc(a["route_label"])} &rarr;</a></div>'
              + f'<p class="why"><span class="lbl">Angle</span>{esc(a["angle"])}</p>'
              + '<div class="note-row"><label><span class="lbl">Live link / notes</span>'
              + '<input type="text" class="cnote" placeholder="pitch sent date, editor name, live URL"></label></div>'
              + '</article>')
    return ''.join(out)

def render_replies_pane():
    import reply_engine as RE
    out = ['<section class="panel" data-keep="1"><h3>How the reply center works</h3>'
           '<p>The Reply Desk task reads the LinkedIn notification mail four times a weekday, classifies '
           'every reply against the categories below, and publishes drafted answers to its page. This tab is '
           'the same engine in reference form: find the category, read the style and state adjustments, copy '
           'the template, fill the braces, send by hand. Log the category letter in the send log note.</p>'
           '<p class="hint">Filter, then copy. Braces like {first} are yours to fill; nothing sends itself.</p>'
           '<input type="search" id="rfilter" placeholder="Filter everything: not my desk, warranty, budget, R4..." aria-label="Filter reply library"></section>']
    out.append('<h3 class="wk">Triage: every reply lands in one of these</h3>')
    for c in RE.REPLY_CATEGORIES:
        resp2 = ''
        if c.get('response_to_referred'):
            resp2 = ('<div class="draft"><div class="draft-bar"><div class="tabs"><span class="tab is-on">To the referred person</span></div>'
                     '<button class="copy ccopy" type="button">Copy</button></div>'
                     f'<div class="msg postbody"><p>{esc(c["response_to_referred"])}</p></div>'
                     f'<script type="application/json" class="ctext">{jsafe(c["response_to_referred"])}</script></div>')
        out.append(f'<article class="row post rc" data-cid="RC-{esc(c["id"])}">'
          + f'<header class="row-head"><div class="who"><h2>{esc(c["id"])}. {esc(c["category"])}</h2>'
          + f'<p class="role">Sounds like: {esc(c["cues"])}</p></div></header>'
          + f'<p class="why"><span class="lbl">Do this</span>{esc(c["action"])}</p>'
          + '<div class="draft"><div class="draft-bar"><div class="tabs"><span class="tab is-on">Reply template</span></div>'
          + '<button class="copy ccopy" type="button">Copy</button></div>'
          + f'<div class="msg postbody"><p>{esc(c["response"])}</p></div>'
          + f'<script type="application/json" class="ctext">{jsafe(c["response"])}</script></div>'
          + resp2
          + f'<p class="hint"><b>Then:</b> {esc(c["next"])} <b>Handoff:</b> {esc(c["handoff"])}</p></article>')
    out.append('<h3 class="wk">Decision styles: match the reply to the reader</h3>')
    for s in RE.DECISION_STYLES:
        out.append(f'<article class="row post rc"><header class="row-head"><div class="who"><h2>{esc(s["style"])}</h2>'
          + f'<p class="role">Tells: {esc(s["tells"])}</p></div></header>'
          + f'<p class="why"><span class="lbl">Adjust</span>{esc(s["modifier"])}</p>'
          + '<div class="draft"><div class="draft-bar"><div class="tabs"><span class="tab is-on">In practice</span></div>'
          + '<button class="copy ccopy" type="button">Copy</button></div>'
          + f'<div class="msg postbody"><p>{esc(s["example"])}</p></div>'
          + f'<script type="application/json" class="ctext">{jsafe(s["example"])}</script></div></article>')
    out.append('<h3 class="wk">Buyer states, and the one question per message rule</h3>')
    rows = ''.join(f'<article class="row post rc"><header class="row-head"><div class="who"><h2>{esc(s["state"])}</h2>'
        + f'<p class="role">Cues: {esc(s["cues"])}</p></div></header>'
        + f'<p class="why"><span class="lbl">Adjust</span>{esc(s["adjust"])}</p></article>' for s in RE.BUYER_STATES)
    out.append(rows)
    out.append('<section class="panel"><h3>Qualification, one per message</h3><ol>'
      + ''.join(f'<li><b>{esc(q["field"])}:</b> {esc(q["question"])} <i>{esc(q["why"])}</i></li>' for q in RE.QUALIFICATION)
      + '</ol></section>')
    out.append('<section class="panel"><h3>Who takes the handoff</h3><div class="twrap"><table><thead><tr><th>When the conversation is</th><th>Owner</th><th>Backup</th></tr></thead><tbody>'
      + ''.join(f'<tr><td>{esc(h["trigger"])}</td><td>{esc(h["owner"])}</td><td>{esc(h["backup"])}</td></tr>' for h in RE.HANDOFF)
      + '</tbody></table></div></section>')
    out.append('<h3 class="wk">Content engagement: replies in public</h3>')
    out.append('<section class="panel"><p>The categories above answer outreach. These cover people '
      'who engage with a post before any DM goes out, which are the warmest contacts the program '
      'produces and the only ones whose replies their whole network can see. No templates on '
      'purpose: a comment reply that reads like it came from a library is worse than staying quiet.</p></section>')
    for e in RE.ENGAGEMENT:
        out.append(f'<article class="row post rc"><header class="row-head"><div class="who">'
          + f'<h2>{esc(e["when"])}</h2></div></header>'
          + f'<p class="why"><span class="lbl">Do this</span>{esc(e["do"])}</p>'
          + f'<p class="hint"><b>Discipline:</b> {esc(e["discipline"])}</p></article>')
    out.append('<section class="panel"><h3>What to give someone who engaged</h3><ol>'
      + ''.join(f'<li>{esc(g)}</li>' for g in RE.ENGAGEMENT_GIVES) + '</ol></section>')
    out.append('<h3 class="wk">Objections, answered short</h3>')
    for o in RE.OBJECTIONS:
        out.append(f'<article class="row post rc"><header class="row-head"><div class="who"><h2>{esc(o["q"])}</h2></div></header>'
          + '<div class="draft"><div class="draft-bar"><div class="tabs"><span class="tab is-on">Answer</span></div>'
          + '<button class="copy ccopy" type="button">Copy</button></div>'
          + f'<div class="msg postbody"><p>{esc(o["a"])}</p></div>'
          + f'<script type="application/json" class="ctext">{jsafe(o["a"])}</script></div></article>')
    return ''.join(out)

# ---------------------------------------------------------------------------
# CSS and JS the desk template splices in. Plain strings, no f-strings, so braces are safe.
# ---------------------------------------------------------------------------
STUDIO_CSS = """
.tabrail{display:flex;gap:2px;margin:0;padding:0 0 0;overflow-x:auto}
.tabrail button{font-family:inherit;font-size:12px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;
  background:transparent;color:var(--ink-2);border:0;border-bottom:3px solid transparent;padding:10px 14px;cursor:pointer;white-space:nowrap}
.tabrail button.is-on{color:var(--ink);border-bottom-color:var(--copper)}
.tabrail button:hover{color:var(--ink)}
.pane{display:none}.pane.is-on{display:block}
.wk{font-size:13px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--ink-3);margin:26px 0 10px}
.postbody p{margin:0 0 12px}.postbody p:last-child{margin-bottom:0}
.postbody .cta{font-weight:600}
.tagline{color:var(--ink-3);font-size:14px}
.factline{margin:12px 0 0;font-size:13px;color:var(--ink-2);line-height:1.55}
.factline i{color:var(--ink-3);font-style:normal}
.asset{display:flex;gap:14px;margin-top:12px;align-items:flex-start;flex-wrap:wrap}
.asset-fr{width:230px;flex:0 0 auto;border:1px solid var(--line);background:var(--paper)}
.asset-fr svg{display:block;width:100%;height:auto}
.asset-side{flex:1 1 220px;min-width:200px}
.asset-side .hint{margin-top:0}
.slides{display:flex;gap:8px;overflow-x:auto;padding-bottom:6px;flex:1 1 100%;max-width:100%}
.slide{flex:0 0 168px;border:1px solid var(--line)}
.slide svg{display:block;width:100%;height:auto}
.chip-ch-company{background:var(--navy-soft);color:var(--navy);border-color:transparent}
.chip-ok{background:var(--good-soft);color:var(--good);border-color:transparent}
.chip-warn{background:var(--copper-soft);color:var(--copper);border-color:transparent}
.cstat{font-family:inherit;font-size:13px;font-weight:600;padding:6px 8px;background:var(--card);color:var(--ink);border:1px solid var(--line-2)}
#rfilter{width:100%;margin-top:12px;font-family:inherit;font-size:14px;padding:9px 11px;background:var(--paper);border:1px solid var(--line-2);color:var(--ink)}
.twrap{overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:13px;margin-top:8px}
th{ text-align:left;font-size:11px;letter-spacing:.07em;text-transform:uppercase;color:var(--ink-3);padding:6px 10px 6px 0;border-bottom:1px solid var(--line-2)}
td{padding:8px 10px 8px 0;border-bottom:1px solid var(--line);color:var(--ink-2);vertical-align:top;line-height:1.5}
.rc .row-head{margin-bottom:2px}
.is-filtered{display:none}
#printhost{display:none}
@media print{
  body.printing .app-root{display:none}
  body.printing #printhost{display:block}
  #printhost svg{width:100%;height:auto;page-break-after:always;display:block}
  @page{size:216mm 270mm;margin:0}
}
@media (max-width:720px){.asset-fr{width:100%}.slides .slide{flex-basis:140px}}
"""

STUDIO_JS = """
// ---- top level tabs -------------------------------------------------------
(function(){
  var rail=document.getElementById('tabrail'); if(!rail) return;
  var btns=rail.querySelectorAll('button');
  function show(id){
    Array.prototype.forEach.call(btns,function(b){ var on=b.getAttribute('data-pane')===id;
      b.classList.toggle('is-on',on); b.setAttribute('aria-selected',on?'true':'false'); });
    Array.prototype.forEach.call(document.querySelectorAll('.pane'),function(p){ p.classList.toggle('is-on',p.id==='pane-'+id); });
    document.body.classList.toggle('tab-other', id!=='outreach');
    try{ sessionStorage.setItem('hustad-tab',id); }catch(e){}
  }
  Array.prototype.forEach.call(btns,function(b){ b.addEventListener('click',function(){ show(b.getAttribute('data-pane')); }); });
  var t=null; try{ t=sessionStorage.getItem('hustad-tab'); }catch(e){}
  show(t && document.getElementById('pane-'+t) ? t : 'outreach');
})();
// ---- content state: posted ticks, statuses, notes -------------------------
function cent(id){ return (state.content=state.content||{})[id]||{}; }
function setCent(id,patch){ var m=(state.content=state.content||{}), e=m[id]||{}, k;
  for(k in patch) e[k]=patch[k]; e.ts=Date.now(); m[id]=e; lswrite(state); saveSoon(); paintContent();
  if (typeof sbUpsertContent==='function') sbUpsertContent(id,e); }
function paintContent(){
  Array.prototype.forEach.call(document.querySelectorAll('[data-cid]'),function(el){
    var e=cent(el.getAttribute('data-cid'));
    el.classList.toggle('is-done',!!e.done);
    var c=el.querySelector('.cchk'); if(c) c.checked=!!e.done;
    var n=el.querySelector('.cnote'); if(n && n.value!==(e.note||'') && document.activeElement!==n) n.value=e.note||'';
    var s=el.querySelector('.cstat'); if(s && e.status && s.value!==e.status) s.value=e.status;
  });
}
(function(){
  Array.prototype.forEach.call(document.querySelectorAll('[data-cid]'),function(el){
    var id=el.getAttribute('data-cid');
    var c=el.querySelector('.cchk'); if(c) c.addEventListener('change',function(ev){
      setCent(id,{done:ev.target.checked, at:new Date().toISOString().slice(0,16)}); });
    var n=el.querySelector('.cnote'); if(n) n.addEventListener('input',function(ev){ setCent(id,{note:ev.target.value}); });
    var s=el.querySelector('.cstat'); if(s) s.addEventListener('change',function(ev){ setCent(id,{status:ev.target.value}); });
  });
  // one handler per draft block: the button copies its own block's payload, nothing else's
  Array.prototype.forEach.call(document.querySelectorAll('.draft'),function(d){
    var cp=d.querySelector('.ccopy'), tx=d.querySelector('.ctext');
    if(cp && tx){ cp.addEventListener('click',function(){
      navigator.clipboard.writeText(JSON.parse(tx.textContent)).then(function(){
        cp.textContent='Copied'; cp.classList.add('ok');
        setTimeout(function(){ cp.textContent='Copy'; cp.classList.remove('ok'); },1400); }); }); }
  });
  paintContent();
})();
// ---- PNG / SVG download for graphic assets --------------------------------
function saveNamed(name,blob){ try{ var u=URL.createObjectURL(blob), a=document.createElement('a');
  a.href=u; a.download=name; document.body.appendChild(a); a.click();
  setTimeout(function(){ URL.revokeObjectURL(u); a.parentNode&&a.parentNode.removeChild(a); },0); }catch(e){} }
(function(){
  Array.prototype.forEach.call(document.querySelectorAll('.dlsvg'),function(b){
    b.addEventListener('click',function(){ var svg=b.closest('.asset').querySelector('svg');
      var s=new XMLSerializer().serializeToString(svg);
      saveNamed(b.getAttribute('data-name'),new Blob([s],{type:'image/svg+xml'})); }); });
  Array.prototype.forEach.call(document.querySelectorAll('.dlpng'),function(b){
    b.addEventListener('click',function(){
      var svg=b.closest('.asset').querySelector('svg');
      var vb=svg.getAttribute('viewBox').split(' '), w=+vb[2], h=+vb[3];
      var s=new XMLSerializer().serializeToString(svg);
      var img=new Image();
      img.onload=function(){ var c=document.createElement('canvas'); c.width=w*2; c.height=h*2;
        var x=c.getContext('2d'); x.drawImage(img,0,0,c.width,c.height);
        c.toBlob(function(bl){ if(bl) saveNamed(b.getAttribute('data-name'),bl); },'image/png'); };
      img.src='data:image/svg+xml;charset=utf-8,'+encodeURIComponent(s); }); });
})();
// ---- carousel print to PDF ------------------------------------------------
(function(){
  var host=document.getElementById('printhost');
  Array.prototype.forEach.call(document.querySelectorAll('.prslides'),function(b){
    b.addEventListener('click',function(){
      host.innerHTML='';
      Array.prototype.forEach.call(b.closest('.asset').querySelectorAll('.slide svg'),function(svg){
        host.appendChild(svg.cloneNode(true)); });
      document.body.classList.add('printing');
      var done=function(){ document.body.classList.remove('printing'); host.innerHTML='';
        window.removeEventListener('afterprint',done); };
      window.addEventListener('afterprint',done);
      window.print(); }); });
})();
// ---- reply library filter -------------------------------------------------
(function(){
  var f=document.getElementById('rfilter'); if(!f) return;
  var cards=document.querySelectorAll('#pane-replies .row, #pane-replies .panel:not([data-keep]), #pane-replies .wk');
  f.addEventListener('input',function(){
    var q=f.value.trim().toLowerCase();
    Array.prototype.forEach.call(cards,function(el){
      if(el.classList.contains('wk')||el.classList.contains('panel')){ el.classList.toggle('is-filtered',!!q); return; }
      el.classList.toggle('is-filtered', q && el.textContent.toLowerCase().indexOf(q)<0); });
  });
})();
// ---- content log export ---------------------------------------------------
(function(){
  var b=document.getElementById('copycontent'); if(!b) return;
  b.addEventListener('click',function(){
    var rows=[['Id','Done','At','Status','Note']], m=state.content||{};
    Object.keys(m).sort().forEach(function(k){ var e=m[k];
      rows.push([k,e.done?'Y':'',e.at||'',e.status||'',e.note||'']); });
    var t=rows.map(function(r){ return r.map(function(v){ return String(v==null?'':v).replace(/[\\t\\n]/g,' '); }).join('\\t'); }).join('\\n');
    navigator.clipboard.writeText(t).then(function(){ b.textContent='Copied';
      setTimeout(function(){ b.textContent='Copy content log'; },1400); }); });
})();
"""

def build(cal):
    """Everything build_desk.py needs, as one dict of strings."""
    return {
      'css': STUDIO_CSS,
      'js': STUDIO_JS,
      'replies': render_replies_pane(),
      'posts': render_posts_pane(cal),
      'newsletter': render_newsletter_pane(cal),
      'articles': render_articles_pane(cal),
    }
