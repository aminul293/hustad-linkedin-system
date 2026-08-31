"""Write Reply_Engine.md from reply_engine.py so the markdown and the workbook never disagree."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
from reply_engine import REPLY_CATEGORIES, DECISION_STYLES, BUYER_STATES, QUALIFICATION, HANDOFF, MEETING_SET, REFERRAL_ASKS, OBJECTIONS
L = []
w = L.append
w("# Hustad LinkedIn New Business Track: Reply Engine\n")
w("How to read a reply, what to say back, and who owns the next step. Cold new business only. "
  "Anyone whose current employer is on the 2026 opportunity list is out of this program; that is warm outreach and it runs separately.\n")
w("Two rules that override everything below. Hustad does not do ground up construction, so nothing here offers it. "
  "And when someone turns out to have worked at a company Hustad serves, Eric stays in that conversation himself. "
  "There is no internal handoff for shared history.\n")
w("## A. Reply categories\n")
for c in REPLY_CATEGORIES:
    w(f"### {c['id']}. {c['category']}\n")
    w(f"**Cues.** {c['cues']}\n")
    w(f"**What to do.** {c['action']}\n")
    w(f"**Reply.**\n\n> {c['response']}\n")
    w(f"**Next.** {c['next']}\n")
    w(f"**Handoff.** {c['handoff']}\n")
w("## B. Decision styles\n")
for d in DECISION_STYLES:
    w(f"### {d['style']}\n")
    for k, v in d.items():
        if k == 'style': continue
        w(f"**{k.replace('_',' ').title()}.** {v}\n")
w("## C. Buyer states\n")
for b in BUYER_STATES:
    w(f"### {b.get('state', b.get('id',''))}\n")
    for k, v in b.items():
        if k in ('state','id'): continue
        w(f"**{k.replace('_',' ').title()}.** {v}\n")
w("## D. Qualification\n")
for q in QUALIFICATION:
    if isinstance(q, dict):
        w("- " + " | ".join(f"**{k.replace('_',' ').title()}:** {v}" for k, v in q.items()) + "\n")
    else:
        w(f"- {q}\n")
w("## E. Handoff routing\n")
w("| When | Who | What they get |\n|---|---|---|")
for h in HANDOFF:
    vals = list(h.values())
    w("| " + " | ".join(str(v).replace('|', '/') for v in (vals + ['', '', ''])[:3]) + " |")
w("")
w("## F. Meeting scripts\n")
for k, v in MEETING_SET.items():
    w(f"**{k.replace('_',' ').title()}.**\n\n> {v}\n")
w("## G. Referral asks\n")
for r in REFERRAL_ASKS:
    w(f"**{r['when']}.**\n\n> {r['copy']}\n")
w("## H. Objections\n")
for o in OBJECTIONS:
    w(f"**{o['q']}**\n\n> {o['a']}\n")
open(paths.s(paths.FOLDER / 'Reply_Engine.md'), 'w').write("\n".join(L))
import shutil; shutil.copy(paths.s(paths.FOLDER / 'Reply_Engine.md'), paths.s(paths.OUT / 'Reply_Engine.md'))
print('wrote Reply_Engine.md', len("\n".join(L)), 'chars |', len(REPLY_CATEGORIES), 'categories')
