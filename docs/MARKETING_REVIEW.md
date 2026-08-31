# Marketing review

A social execution pass over the content system before handoff, reviewed the way a head of demand
gen would review it: does this earn attention from portfolio and facilities decision makers, and
does it convert attention into the pipeline the DM program feeds on. Findings, what changed, and
what stays deliberately unfashionable.

## Changed in this pass

**The carousels were on the wrong channel.** The original calendar put every designed asset on the
company page because that is where "brand content" conventionally lives. That is backwards for
this program. Company pages earn a fraction of personal profile reach, carousels are the highest
performing format in the calendar, and the Publication Roadmap's stated objective is Eric's
personal authority. The three carousels now publish from Eric's profile as document posts, with
the company page resharing the same day; the stat and checklist cards stay on the company page so
it keeps a pulse, with Eric resharing those in one line of his own words. Side benefit: personal
posts are automatable on the self serve API products, so the flagship format goes fully automatic
before the Community Management approval even lands.

**An engagement protocol now sits at the top of the Posts tab.** Posting into a feed without
participating in it wastes the network. The protocol is fifteen minutes: comment on three to five
operator posts before publishing, answer every comment inside ninety minutes after. The reason it
lives on the tab rather than in a doc: it has to be read on posting mornings, not once.

**One repeated signature phrase varied.** "Urgency theater" appeared twice in eight weeks; the
second instance now reads differently. A voice this plain gets recognized fast, and recognized
phrases start reading as template.

## Judged right as built

**The DM and content calendars are one funnel, and the timing works.** Forty cold DMs a day means
forty profile visits a day from exactly the audience the posts target. A first touch that lands the
same week as the Exterior Risk File carousel reads as "this person publishes useful work," not
"this person wants something." The budget season arc (September condition reads, October capital
planning, the freeze deadline) tracks the same calendar logic the DM copy uses, so a prospect who
reads both sees one coherent operator.

**Saturday stays, with a tripwire.** Saturday B2B reach is thinner, but Eric chose the day, the
Saturday slot carries the human posts (which trade on depth with existing connections, not cold
reach), and weekend feeds have less competition for the audience that does scroll. The tripwire:
if four consecutive Saturday posts underperform the weekday median on comments, move the human
post to Sunday evening and say so in the Friday review.

**Hooks front load tension and survive the fold.** Every hook is under 205 characters (enforced in
QA), states a cost or a contrarian read in the first line, and never opens with "I'm excited to
announce." The two hookiest slots (Tuesday POV, Thursday companion) end in one answerable question;
two Saturday posts deliberately carry no CTA, because asking every time reads as farming.

**The claim discipline is a feature, not a constraint.** Every number traces to a source printed
on the asset itself, no client is ever named, and the roadmap's banned phrases fail the build.
In a feed full of "saves 90 percent" contractors, sourced restraint is the differentiator, and it
is also what makes every post safe to hand to an editor later as a writing sample.

**Newsletter and article sequencing follows the roadmap exactly.** Owned authority first, Tier 1
contributor routes second, buyer media on the strength of the clips. The monthly newsletter theme
feeds that month's posts, each published article gets repurposed into two posts and a carousel,
and no article goes to two outlets at once.

## For the next cycle

1. **Measure comments from the right people, not likes.** A post is working when asset managers
   and facilities directors comment, because commenters are warm DM targets the same week. Log
   result notes in the tab; the Friday review should read the content log beside the send log.
2. **Storm agility.** When a verified event touches two or more target markets, swap the week's
   Tuesday post for a storm documentation post (the C-0922 pattern) and push the planned one a
   week. The Outreach Desk already verifies events every morning; borrow its judgment.
3. **After the first published byline,** pin it, add it to the Featured section, and cut the
   promised carousel from it within a week while the outlet is still promoting it.
4. **Employee amplification, invited not mandated.** A one line Slack note to the BD team when a
   carousel goes out ("reshare if useful") is worth real reach; anything more organized reads as
   astroturf and burns goodwill.
5. **Watch the eight week cliff.** The calendar runs through October 24. The C-1024 post asks
   readers what the next cycle should cover; the answers plus the Friday review numbers are the
   brief for the next `content_engine.py` batch, which should be written in week seven, not week
   nine.


## Addendum: the Content Standards pass (August 27, evening)

Eric supplied the house Content Standards and Voice Guide after this review was written, and it
outranks anything above. A full compliance pass followed: eleven posts carried the guide's number
one banned cadence ("X is not Y. It is Z.") including several hooks this review had praised, two
opened on signpost phrases, and the weekly shape ran text-only days back to back, which the guide's
rotation rule forbids. All rewritten from scratch per the rewrite protocol, not edited around.
Saturdays became real-photo posts (one field photo, compliance checklist on the card, text alone
when nothing clears the bar), question closes were cut to under half and never consecutive, and the
assets were re-skinned to the house system: deep slate, warm white, single sand accent, Lora
display over Poppins, hairline footer. The guide's mechanical rules now live in the build as
`voice_lint()`, so the next "sounds like AI" pattern fails CI instead of reaching Eric.
