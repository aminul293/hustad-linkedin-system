# Hustad LinkedIn New Business Track: copy standard (v2)

The rules a cold first DM has to pass before it enters the send queue. Enforced in code
(copy_engine.qa and the dedup machinery in the rebuild scripts), not just written down.

## The arc, from the Sales Brain

Every touch runs the Playbook arc compressed into a DM:

    Hi {First},
    <blank line>
    their reality: one verified company fact, or the honest line about when we connected
    <blank line>
    evidence translated into their role's consequence
    <blank line>
    the give from the role stack, and one small ask with the exit open

**The first ask is the give, never a meeting.** Owners get the one-page capital view sample,
asset managers the two-page property summary, operations the fall checklist, construction the
bid leveling example, procurement the standards one-pager, acquisitions a sample condition read.
The meeting ask lives in Touch 3. Touch 2 offers a DIFFERENT give than Touch 1 (mostly the
warranty enforceability one-pager), so the follow-up is a second gift, not a rename.

About a third of first touches run the Play 12 budget season bridge: "when next year's exterior
numbers get built, is there a current condition read behind them, or is it mostly age and
invoices?" It is the highest-fit question in the library from late August through November.

## Three rules that override everything else

**Hustad does not do new construction.** No ground-up, no owner's representation on new builds,
no warranty-at-turnover. Purely-development roles are not targets. Construction titles at owner
operators stay, and their copy says "occupied" out loud. Companies whose operating book is young
and self-built (Hillpointe, Roers, Continental, Thompson Thrift, Sentral, Mark-Taylor, Madison,
Up Campus) get a documentation-and-warranty-upkeep story; an aging-roof story tells them we do
not know their portfolio.

**Past employment at a Hustad client is Eric's own opener.** The shared history draft with the
[CLIENT] placeholder, sent by Eric, only when the profile shows the employer and the tenure
overlaps our work there. Never an internal handoff. R21 in the reply engine says the same.

**Every give is a sample we can actually send.** A redacted page from a real program. Never an
offer to grade or map their portfolio sight unseen: that is an inspection engagement wearing a
give's clothes, and it reads as bait.

## What fails QA

Over 90 words (median lands near 78). More than one question, or none. A dash, an exclamation
mark, a hyphenated numeric range. No contraction anywhere. Fewer than three paragraph blocks or
missing blank lines. Banned vocabulary (the corporate register and the cold-email tells), the
stale-phrase list from earlier versions, cornering language ("is this not where your attention
is"), and any ground-up construction language.

## What fails on repetition

Within one send day: any two messages sharing an opening line, a middle block, a closing ask, or
the closing ask's final sentence. Within one company family (Harbor Group Management and Harbor
Group International are one family): any two people ever sharing an opening line or middle block.
Plan-wide: no block used more than 8 times, and the give phrasings rotate so the same product
description never shows up three times in a day.

## What no linter can check

One thing about their company that is true, specific, sourced, and worth their attention, from
hooks.py, which traces to data/research/companies_research.json, which carries source URLs. If there is no
verified fact, open on the segment reality or the honest connection line. Never on an invented
fact, and never on a stat pile: one number per opener.
