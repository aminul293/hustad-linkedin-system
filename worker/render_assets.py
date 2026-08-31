#!/usr/bin/env python3
"""
Render the calendar's designed assets to files the worker (or a human) can post:
  graphic  -> data/out/assets/<id>.png   (2x raster of the SVG card)
  carousel -> data/out/assets/<id>.pdf   (one slide per page, the LinkedIn document format)

Uses headless Chromium via Playwright, which CI already has for tests, so there is no native
SVG rasterizer dependency to manage. The Command Center page produces identical files by hand
(Download PNG, Print slides), so nothing here is load bearing for a human-run week.

Run:  python3 worker/render_assets.py            all assets, skipping ones already rendered
      python3 worker/render_assets.py --force    re-render everything
"""
import sys, os, json, base64
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'pipeline'))
import paths, studio

OUT = paths.OUT / 'assets'

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Lora:wght@500;600'
         '&family=Poppins:wght@400;500;600&display=swap">')

PDF_SHELL = ('<!doctype html><html><head><meta charset="utf-8">' + FONTS + '<style>'
             '@page{size:216mm 270mm;margin:0} body{margin:0}'
             'svg{display:block;width:216mm;height:270mm;page-break-after:always}'
             '</style></head><body>{slides}</body></html>')

PNG_SHELL = ('<!doctype html><html><head><meta charset="utf-8">' + FONTS + '<style>'
             'body{margin:0} svg{display:block;width:1200px;height:1500px}'
             '</style></head><body>{svg}</body></html>')

def main():
    force = '--force' in sys.argv
    cal_path = paths.WORK / 'content_calendar.json'
    if not cal_path.exists():
        print('no content calendar; run: python3 pipeline/content_engine.py'); return 1
    cal = json.load(open(cal_path))
    os.makedirs(OUT, exist_ok=True)
    jobs_png, jobs_pdf = [], []
    for p in cal['posts']:
        a = p.get('asset') or {}
        if a.get('template') in ('stat', 'check'):
            f = OUT / f"{p['id']}.png"
            if force or not f.exists():
                svg = studio.svg_stat(a) if a['template'] == 'stat' else studio.svg_check(a)
                jobs_png.append((p['id'], svg, f))
        elif a.get('template') == 'carousel':
            f = OUT / f"{p['id']}.pdf"
            if force or not f.exists():
                jobs_pdf.append((p['id'], studio.svg_slides(a), f))
    if not jobs_png and not jobs_pdf:
        print('all assets current'); return 0
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        b = pw.chromium.launch(args=['--no-sandbox'])
        pg = b.new_page(device_scale_factor=2)   # match the page's 2x PNG export
        def load(html):
            pg.goto('data:text/html;base64,' + base64.b64encode(html.encode()).decode())
            try:
                pg.evaluate('document.fonts.ready')   # Lora and Poppins, before any pixel is taken
                pg.wait_for_timeout(150)
            except Exception:
                pass   # offline: system fallbacks render, which is better than failing the run
        for pid, svg, f in jobs_png:
            pg.set_viewport_size({'width': 1200, 'height': 1500})
            load(PNG_SHELL.replace('{svg}', svg))
            pg.locator('svg').screenshot(path=str(f))
            print(f'{pid}: {f}')
        for pid, slides, f in jobs_pdf:
            load(PDF_SHELL.replace('{slides}', ''.join(slides)))
            pg.pdf(path=str(f), prefer_css_page_size=True)
            print(f'{pid}: {f} ({len(slides)} pages)')
        b.close()
    return 0

if __name__ == '__main__':
    sys.exit(main())
