"""
Copy engine v3. The Sales Brain applied to a cold first-degree DM.

Every Touch 1 follows the Playbook arc, compressed: Open (their reality), Substance (evidence
translated into their role's consequence), Path (the give from the role stack), Ask (one small
CTA with the exit open). The first ask is the give, never the meeting; the meeting is Touch 3's
job. 90 words is the ceiling and a target of 55 to 80. One question per message, ever.

Hard rules preserved from v2: Hustad does not do new construction; past employment at a client
is Eric's own opener; no phrase repeats within a send day; no two people at the same company
open on the same sentence; blank lines between paragraphs; everything traced to hooks.py.
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
import re, json, hashlib, pandas as pd
from hooks import HOOKS, HOOK_ALT

WORD_CEILING = 90
WORD_FLOOR   = 40

# Companies whose operating book is young and self-built: the roof story is documentation and
# warranty upkeep, not decay. Decay language reads as not knowing their portfolio.
YOUNG_BOOK = {'Hillpointe', 'Roers Companies', 'Continental Properties', 'Thompson Thrift',
              'Madison Communities', 'Up Campus Student Living', 'Mark-Taylor, Inc.', 'Sentral'}
YOUNG_MEANING = [
 "On product that young, the roof job is mostly discipline: baseline documentation, warranties kept enforceable, and storm response with a record that holds up.",
 "Young roofs don't need rescue, they need a record: documented baselines, warranty terms kept current, and storm damage caught while it's still a claim.",
 "The file you'll want on those roofs in year twelve gets built now, and it's cheap to build: baselines, warranty upkeep, and a clean storm record.",
]
CLEARED_PROOF = {
    'Student housing': 'Cardinal Group and Yugo',
    'Senior living': 'Dial Retirement Communities and Charter Senior Living',
    'Military housing': 'Burlington Capital at Offutt',
    'Multifamily': 'Asset Living',
    'Affordable multifamily': 'Asset Living',
    'Build to rent': 'Asset Living',
    'Single family rental': 'Asset Living',
    'Multifamily / Commercial': 'Asset Living',
    'Commercial': '', 'Retail': '', 'Industrial': '', 'HOA / Condo': '',
    'Hospitality': '', 'Healthcare': '', 'Manufactured housing': '',
}

# ---------------------------------------------------------------------------
# Substance: role-tied meaning with the evidence inside it. {proof} optional.
# ---------------------------------------------------------------------------
MEANING_LANE = {
 'Ownership / Executive': [
   "The exterior line is usually the shakiest number in the plan. We put a condition grade, the spend history and a budget range behind it, building by building.",
   "Open roof items have a way of drifting until they're capital. We grade and price every one, and the small stuff gets fixed on the same visit under a cap you set.",
   "What owners hire us for is visibility: which roofs are fine, which need watching, and which are closer to capital than anyone's put in writing.",
   "We run the roof and exterior side for operators like {proof}: scheduled inspections, same-visit repairs under a pre-approved cap, and a straight read on what's a repair and what's capital.",
   "The published maintenance benchmarks are blunt: proactively maintained roofs run years longer and cost less over the hold than reactive-only. The catch is that nobody's sure which of theirs is which.",
 ],
 'Asset management': [
   "Most capital plans carry the roof line as age plus the last invoice, and that doesn't survive the first hard question. We replace it with a current condition read per building.",
   "The repair versus capital call is the whole line. We make it in writing, with photos, before the number lands in the plan; that's what we do for {proof}.",
   "The maintenance studies are blunt: proactive programs run about 14 cents a square foot a year against 25 for reactive, and the roofs last about eight years longer. The hard part's knowing which bucket each of yours sits in.",
   "Condition grade, spend history, remaining life and a budget range, two pages per property. It's the difference between defending the number and re-deriving it in the meeting.",
 ],
 'Facilities / Maintenance': [
   "The calls that repeat are the ones where the first visit was a patch and the record was a photo on somebody's phone. We document and price every deficiency, and fix the small ones while we're up there.",
   "Same-visit repairs under a pre-approved cap do most of the work: your team isn't booking a second trip and a second invoice for the same leak.",
   "One inspection format across every property, photos by building, and the small stuff closed out on the visit; that's the program we run for {proof}.",
   "Leak calls don't schedule themselves politely. A standing inspection route with a repair cap means most of them never get made, and the ones that do come with a file attached.",
 ],
 'CapEx / Construction': [
   "When three bids get written three different ways, the low one's rarely the cheapest by closeout. We write one owner scope by trade and level everything against it.",
   "Hidden conditions and change orders are where exterior budgets die. We photo-document concealed conditions before work continues, priced at rates set up front.",
   "We run capital roof and exterior on occupied properties: the condition read, the scope, phasing around residents, and daily photo logs while it's running.",
 ],
 'VP / Director Operations': [
   "One standard across regions is most of the value: a roof report out of one region reads like the next, and no regional's negotiating their own version.",
   "Roof items should show up on a list, not as emergencies. Scheduled inspections and same-visit repairs are how that happens; that's what we run for {proof}.",
   "What operations feels first is fewer repeat tickets, and a report a regional can act on that doesn't need a translator.",
 ],
 'Regional / Portfolio': [
   "What regionals get from us is a short list per property: urgent, watch, capital, with photos, so the same leak doesn't surprise anyone twice.",
   "Your sites get one number to call, and you get one open-items list instead of a stack of proposals that don't talk to each other.",
 ],
 'Procurement / Risk': [
   "Carriers keep asking for current roof condition at renewal, and almost nobody can produce it building by building. We can.",
   "One agreement, one inspection standard, itemized closeouts, and a not-to-exceed on small repairs so they don't come back as change orders.",
 ],
 'Site level': [
   "Inspections, leak calls, storm response, and the small stuff fixed on the visit instead of written up and scheduled for later. It's most of what keeps a roof cheap.",
 ],
}
MEANING_SEGMENT = {
 'Student housing': [
   "We baseline every student roof on the first visit, fix what's fixable while we're there, and flag what has to land before next August; that's how we run it for Cardinal Group and Yugo.",
   "Acquired student assets show up with a roof history nobody's walked and a turn calendar that doesn't move. We do the walking; Cardinal Group and Yugo are the references.",
   "Student roofs age on a school calendar: hard use, fixed windows, and a capital plan that can't slip a semester. We keep the condition file current so the plan doesn't have to guess.",
 ],
 'Senior living': [
   "Everything up there has to happen without residents noticing, which comes down to sequencing and crews who've done it before. We run that for Dial Retirement Communities and Charter Senior Living.",
   "Crews stage quiet, work around residents, staff and dining hours, and small items get fixed on the inspection visit instead of a second mobilization; that's our program with Dial Retirement Communities.",
 ],
 'HOA / Condo': [
   "Boards don't approve roofs, they approve documents. We photograph, grade and price every deficiency by building and hand the manager something a board can vote on.",
   "Deferred association roofs come back as special assessments. Our per-building report is how managers keep that conversation ahead of the curve.",
 ],
 'Retail': [
   "Tenant hours set the work windows, so we work around them, document by building, and hand ownership one open-items list that's actually current.",
 ],
 'Industrial': [
   "Most of what goes wrong up there is traffic and penetrations, and it's found late. Scheduled inspections and roof-use discipline are the whole game.",
 ],
 'Military housing': [
   "Occupied family housing needs quiet crews and documentation that survives an audit; that's our program with Burlington Capital at Offutt.",
 ],
 'Build to rent': [
   "Hundreds of individual roofs means the money's in small items and truck rolls. We route the inspections and fix what's fixable on the visit.",
 ],
 'Single family rental': [
   "Hundreds of individual roofs means the money's in small items and truck rolls. We route the inspections and fix what's fixable on the visit.",
 ],
}

# ---------------------------------------------------------------------------
# Path: the give, straight from the Sales Brain role stacks. First ask = the give.
# ---------------------------------------------------------------------------
GIVE = {
 'Ownership / Executive': (["the one-page capital view we build for ownership, every roof graded with the repair versus capital call on one sheet",
    "the one-page capital view we build for owners: each roof graded, repair or capital, on a single sheet",
    "a sample of the one-page roof view we build for owners, a real portfolio, redacted",
    "a redacted sample of our one-page portfolio roof view, graded building by building"],
   "a real program we run now, redacted"),
 'Asset management': (["the two-page property summary we build for asset managers: condition grade, spend history and a budget range",
    "the two-page read we build per property, condition grade, spend history and a budget range",
    "a sample of the two-page property summary, grade, history and a budget range on one sheet of paper, front and back"],
   "a real program we run now, redacted"),
 'Facilities / Maintenance': (["the fall roof and exterior checklist our crews work from on occupied properties",
    "the fall checklist our inspectors actually use on occupied properties",
    "our fall roof and exterior checklist, the working version, not the marketing one"],
   "what our inspectors actually find this time of year"),
 'CapEx / Construction': (["a scope and leveling example where the low bid ended up the most expensive offer on the table",
    "a real bid leveling where the low number turned out to be the most expensive offer on the table",
    "a scope and leveling sample from a real exterior package"],
   "a real leveling of three exterior proposals against one owner scope"),
 'VP / Director Operations': (["the fall roof and exterior checklist we use with regional teams",
    "the fall checklist our regional teams run",
    "our fall roof and exterior checklist, the field version"],
   "what our inspectors actually find this time of year"),
 'Regional / Portfolio': (["a one-page sample of the inspection report your regionals would get",
    "a sample of the one-page report your regionals would see from us",
    "one page of what an inspection report from us looks like"],
   "a redacted report from a program we run now"),
 'Procurement / Risk': (["our inspection and documentation standards one-pager",
    "the one-pager on our inspection and documentation standards",
    "our standards sheet, report format, photo record and closeout in one page"],
   "the report format, photo record and closeout package we run under portfolio agreements"),
 'Site level': (["the fall roof and exterior checklist",
    "our fall checklist"],
   "what our inspectors find on occupied properties each fall"),
}
GIVE_SEGMENT = {
 'Senior living': (["the roof and exterior checklist we use with senior living operators, including how we stage crews around residents",
    "the senior living version of our fall checklist, crew staging around residents included"],
   "what our teams see on occupied campuses every fall"),
 'Student housing': (["the post-turn roof and exterior checklist we use with student operators",
    "the post-turn checklist we run with student housing teams"],
   "what turn inspections surface every August"),
 'HOA / Condo': (["a sample of the per-building condition report we give association managers to take to a board",
    "a sample of the board-ready condition report we build per building"],
   "a redacted report from a program we run now"),
}
GIVE_ACQ = (["a sample condition read from a recent acquisition", "the condition read we put together on a recent acquisition, redacted"], "a redacted read from a real deal")

# ---------------------------------------------------------------------------
# Shapes
# ---------------------------------------------------------------------------
BRIDGE_LANES = {'Ownership / Executive', 'Asset management', 'VP / Director Operations',
                'Regional / Portfolio', 'Procurement / Risk', 'CapEx / Construction'}
BRIDGE_Q = [
 "Budget season question: when next year's exterior numbers get built, is there a current condition read behind them, or is it mostly age and invoices?",
 "Quick budget season question: as the 2027 capital lists come together, are the roof numbers backed by a current condition read, or age plus the last invoice?",
 "A budget season question: do next year's roof numbers come from a current read of each building, or from age and whatever the last invoice said?",
 "Since it's budget season: when the exterior line gets set, is there a current read on those roofs behind it, or is it running on age and memory?",
 "One budget season question: how many of the roofs behind next year's numbers has anyone actually stood on this year?",
 "It's budget season, so one question: if someone challenged the roof line in next year's plan, is there a condition read behind it, or a guess with history?",
 "Budget season question while the numbers are still soft: is the roof line built from what's actually up there, or from what it cost last time?",
 "Since the 2027 lists are being built: does the exterior number come from a walk, or from a spreadsheet that's been rolling forward a few years?",
 "A question for budget season: when the roof line gets questioned, what's actually behind it?",
 "Budget season, so worth asking: are next year's roof numbers something you'd defend line by line, or something you'd rather nobody questioned?",
 "One for budget season: does anything in the exterior number come from somebody having been on those roofs this year?",
]
BRIDGE_Q_CAPEX = [
 "Budget season question: when next year's exterior scopes get written, does every bidder price the same document, or does each write their own?",
 "Quick budget season question: on next year's exterior work, is there one owner scope the bids get leveled against, or does the low number pick itself?",
]
BRIDGE_GIVE = [
 "If it'd help, I can send {give}. No meeting required, and if this isn't your desk, a name is plenty.",
 "If it'd be useful, I'll send {give}. Zero strings, and if someone else owns this, point me their way.",
 "Happy to send {give} if that'd help while the numbers are still in pencil.",
 "If it'd help before the numbers lock, I can send {give}.",
 "If it's the second one, I can send {give}. That's usually the fastest fix.",
 "Either way, I can send {give} so you've got something current behind the number.",
]
ASKS_REPORT_ONLY = [
 "Want {give} to hold up against whoever you're using now?",
]
ASKS = [
 "Want me to send {give}?",
 "I can send {give}, zero strings. Useful, or not your desk?",
 "Happy to send over {give}. Want a copy?",
 "If it'd help I'll send {give}. Worth having before the numbers go final?",
 "I can put {give} in front of you this week. Want it?",
 "Can I send {give} your way, or is someone on your team closer to it?",

 "If it'd be useful I can send {give}. Want it in your inbox before the plan goes final?",
 "Easiest test is {give}: I send it, you judge us off that. Want it?",
 "Easiest first step is {give}. Want me to send it?",
 "I can share {give}, no call attached. Interested?",
 "Would {give} be worth a look while the plan's still open?",
 "Can I send {give} and let you decide from there?",
 "I'll send {give} if you want it. If this belongs to someone else, who's the right person?",
]
FORK_ASKS = [
 "Who handles roofs and exteriors for you these days?",
 "How are you handling roof and exterior across the portfolio right now?",
 "If roof and exterior sits with someone else there, who should I be talking to?",
 "Who gets the call when a roof turns into a problem on your side?",
 "Is roof and exterior yours, or does that live with someone else there?",
 "What does the roof and exterior setup look like on your side these days?",
]
RESOURCE_BODY = [
 "Hustad handles roofing and exterior for commercial and multifamily across the country: inspections, service and maintenance, storm response, and capital roof and exterior work. On a portfolio your size the value is visibility, knowing each roof's real condition and what's a repair versus a capital item.",
]
RESOURCE_ASK = "Would like to be your roofing and exterior resource as you grow. What's the best way to get on your vendor list?"

CONN_LINE = [
 (75,  ["Good to connect a few weeks back. I'll keep this short.",
        "Glad we connected recently. I'll keep this quick.",
        "Good to connect the other week. I'll be brief."]),
 (270, ["We connected a few months back and I've kept quiet since, so I'll keep this short.",
        "We connected a few months ago and I haven't made much of it, so I'll keep this short."]),
 (540, ["We connected about a year back and I've kept quiet since, so I'll keep this short."]),
 (9999,["We connected a while back and I've never made much of it, so I'll keep this short."]),
]
IDENTITY = "Hustad's a roofing and exterior contractor for occupied portfolios."

FALLBACK_LANE = {
 'Ownership / Executive': [
   "The exterior line is usually the shakiest number in a capital plan, and rarely the one that gets challenged.",
   "Owners tend to find out about a roof twice: once when it leaks, and once when the invoice lands.",
   "Roof spend shows up as a surprise rather than a plan, and it isn't because anyone was asleep. The information just wasn't there.",
   "Most portfolios carry the roof line as age plus whatever the last invoice was, and it holds up right until something goes wrong.",
   "The difference between a roof that's fine and a roof that's two winters from capital is invisible from the ground.",
   "Deferred roof work doesn't get cheaper while it waits. It just gets reclassified.",
   "On a portfolio your size the roofs are probably fine, and 'probably' is doing a lot of work in that sentence.",
   "Exterior capital moves more between the plan and the actual than almost any other line, and it's the one with the least evidence behind it.",
   "A capital plan with a soft roof number is a plan that gets revised in March.",
   "Every portfolio has a few roofs everyone's worried about and a few nobody should be. The list is rarely the one people carry in their heads.",
 ],
 'VP / Director Operations': [
   "Across a portfolio your size the roof line is rarely one problem. It's forty small ones and two big ones, and telling them apart is most of the work.",
   "Roof condition is the number in an operating budget that gets argued about the most and verified the least.",
   "The roofs that generate calls are almost never the ones anybody was worried about.",
   "Most operators can name their worst roof. Very few can name their second worst, and that's usually the one that goes.",
   "Every region ends up with its own roof vendor and its own idea of what a report looks like, which is fine until you try to compare them.",
   "A roof that's quietly fine and a roof that's quietly failing look identical from the parking lot.",
   "The exterior is the last line anybody looks at and the first one that costs real money when it goes.",
   "Repeat leak calls are usually a records problem before they're a roofing problem.",
   "Nobody budgets for the roof they didn't know about, which is how the exterior line ends up moving mid-year.",
   "By the time a roof reaches an operations meeting it's already expensive.",
 ],
 'Regional / Portfolio': [
   "Regionals usually inherit roof problems rather than choose them.",
   "The same leak getting called in twice says more about the records than the roof.",
   "What a regional wants is a short list per property. What they usually get is a stack of proposals.",
   "Across a spread of properties the hard part isn't fixing roofs, it's knowing which ones to worry about this year.",
   "Site teams call about the roof they can see. The ones that cost money are the ones nobody's been up on.",
   "Roof work across a region tends to run on whoever answered the phone last time.",
   "A roof report should say what to do this week and what to put in the budget. Most say neither.",
   "The properties that generate the most exterior calls are rarely the oldest ones.",
   "Deferred small items don't stay small, and they don't stay on one property.",
   "Most regions have one roof that's about to become somebody's bad quarter.",
 ],
 'Asset management': [
   "Most capital plans carry the roof line as age plus the last invoice, and that doesn't survive the first hard question.",
   "The repair versus capital call on a roof usually gets made by whoever's standing closest to it.",
   "Roof condition is the assumption in a hold period model that gets tested least and moves most.",
   "At disposition the roof file is either there or it isn't, and buyers price that difference.",
   "An exterior number with no condition read behind it is a placeholder wearing a decimal point.",
   "The roofs that break a business plan are the ones that were fine at underwriting.",
   "Nobody argues about the roof line until the year it moves.",
   "A roof either has years left or it doesn't, and age alone is a poor way to tell.",
 ],
 'Facilities / Maintenance': [
   "Repeat leak calls are usually a records problem before they're a roofing problem.",
   "A first visit that was a patch and a record that was a photo on somebody's phone is how the same leak comes back.",
   "Site teams end up managing roof vendors, which isn't in anybody's job description.",
   "Most of what goes wrong on a roof was visible six months earlier to somebody who was looking.",
   "The small stuff is cheap while it's small and expensive about four months later.",
   "A second truck roll for a fifteen minute repair is the most common waste in exterior maintenance.",
   "Maintenance teams usually know exactly which roofs are trouble. What they don't have is the document that proves it.",
   "Leak calls don't arrive politely, and they don't arrive first.",
 ],
 'CapEx / Construction': [
   "When three bids get written three different ways, the low one is rarely the cheapest by closeout.",
   "Exterior scopes go wrong at the scope, not at the price.",
   "Concealed conditions are where exterior budgets actually die.",
   "A roof bid with no owner scope behind it is three contractors pricing three different jobs.",
   "Phasing around residents is most of the cost on an occupied re-roof, and it's usually priced last.",
   "Change orders on exterior work are almost always a scope failure wearing a different name.",
   "The cheapest exterior project is the one that got scoped properly before anyone bid it.",
   "Most capital roof overruns were decided before the work started.",
 ],
 'Procurement / Risk': [
   "Carriers keep asking for current roof condition at renewal, and almost nobody can produce it building by building.",
   "Roof vendors are usually the least standardized line in an otherwise governed vendor program.",
   "The documentation problem on roofs isn't that it doesn't exist. It's that it exists in eleven formats.",
   "A not to exceed on small repairs is the difference between a program and a series of change orders.",
   "Exterior spend is hard to benchmark because almost nobody scopes it the same way twice.",
   "What survives an audit on roof work is the photo record, and it's the thing most often missing.",
 ],
 'Site level': [
   "The small stuff is cheap while it's small.",
   "Most roof calls could have been a scheduled repair three months earlier.",
   "A roof that's leaking has usually been telling somebody for a while.",
 ],
}
FALLBACK_HOOK = {
 'Student housing': [
   "Student assets only give you the one window each August, and whatever doesn't get caught then rides through the school year.",
   "Turn is the only time anybody can really get on a student roof, and it's the same three weeks every year.",
   "On student housing the roof problems don't announce themselves in August. They announce themselves in February.",
   "Student roofs age on a school calendar: hard use, fixed windows, and a capital plan that can't slip a semester.",
 ],
 'Senior living': [
   "On occupied senior campuses the roof work is the easy part. Doing it without residents noticing is the part most people get wrong.",
   "Senior campuses tend to have roofs at three different ages on one site, which makes a single number for the exterior line almost meaningless.",
   "Residents can't move out while a roof gets worked on, so the schedule matters more than the price does.",
 ],
 'HOA / Condo': [
   "On associations the roof is a common element, which turns every deferred repair into a board conversation eventually.",
   "Boards don't approve roofs, they approve documents. The document is usually what's missing.",
   "Association roofs get deferred until they're a special assessment, and by then nobody remembers who first flagged it.",
 ],
 'Retail': [
   "On open-air retail the roof is usually the least consistent line in the whole operating budget: different vendors, different reports, the same leak twice.",
   "Retail roofs are somebody else's problem right up until a tenant's inventory gets wet, and then they're everybody's.",
   "Store hours set the work windows on retail, which rules out most of the vendors who'd otherwise bid it.",
 ],
 'Industrial': [
   "On industrial roofs the damage is almost always traffic and penetrations, and it's almost always found late.",
   "Most of what goes wrong on an industrial roof is somebody else's equipment, installed by somebody who isn't a roofer.",
   "Industrial roofs get walked by everyone except roofers, which is how small stuff turns into a shutdown.",
 ],
 'Build to rent': [
   "Build to rent means hundreds of individual roofs instead of a few big ones, and the small items are where the money actually goes.",
   "Every home in a BTR community carries its own roof, so the exterior line is volume, not one big number.",
   "Scattered product turns roof work into a routing problem before it's a roofing problem.",
 ],
 'Single family rental': [
   "Scattered single family means hundreds of individual roofs, and the small items are where the money goes.",
   "One roof per house means the exterior budget is a thousand small decisions instead of ten big ones.",
   "On scattered rentals the truck roll costs more than the repair about half the time.",
 ],
 'Military housing': [
   "Occupied family housing needs quiet crews and documentation that survives an audit, which narrows the field of who can do the work.",
   "On family housing the paperwork is as much of the job as the roof is.",
   "Military family housing doesn't tolerate a crew that shows up loose. Everything gets documented and closed out clean.",
 ],
}

# ---------------------------------------------------------------------------
# Touch 2 (Play 5) and Touch 3 (Play 6)
# ---------------------------------------------------------------------------
T2_OPEN = [
 "Following up with something useful rather than a nudge.",
 "One follow-up and then I'll leave it alone.",
 "Not chasing you, but I put something together you might get some use out of.",
 "Following up with something instead of a bump.",
]
T2_MID = [
 "It's built from {basis}, and it's the kind of thing that saves a bad surprise at budget time.",
 "It comes straight out of {basis}. Nothing's dressed up, it's just what we actually see there.",
 "It's pulled straight from {basis}, real photos and real numbers rather than a brochure.",
 "It's built from {basis}, and it lines up with the published maintenance benchmarks, the ones showing maintained roofs running years longer than reactive-only.",
]
T2_CLOSE = [
 "Want a copy? No call needed.",
 "Worth sending over?",
 "Happy to send it with no strings. Want it?",
 "Should I send it your way?",
]
TOPIC = {
 'Ownership / Executive': "a current read on how the portfolio's roofs grade out",
 'Asset management': "the repair versus capital call on the roof line",
 'Facilities / Maintenance': "getting ahead of fall and winter roof service",
 'CapEx / Construction': "scope and bid leveling on next year's exterior work",
 'VP / Director Operations': "one roof inspection and service standard across your regions",
 'Regional / Portfolio': "one view of urgent, watch and capital across your properties",
 'Procurement / Risk': "inspection and documentation standards",
 'Site level': "getting ahead of fall roof service",
}
T3_OPEN = ["Last one from me on this.", "Last note from me for a while.", "Closing the loop on this one.", "Last note and then I'm out of your inbox."]
T3_TAIL = [
 "And if it isn't your desk, a name is plenty and I'll leave you alone.",
 "If someone else owns this, point me at them and I'll take it from there.",
 "If it's not you, no problem at all. Just tell me who and I'll go bother them instead.",
 "If this belongs to someone else on your team, a name is all I need.",
]

GIVE2 = {
 'Ownership / Executive': ("the one-pager on how manufacturer roof warranties actually stay enforceable, because most portfolios are quietly voiding theirs", "the warranty maintenance requirements owners rarely see until a claim"),
 'Asset management': ("the fall roof and exterior checklist we run on occupied properties", "what our inspectors actually find this time of year"),
 'Facilities / Maintenance': ("the one-pager on keeping manufacturer roof warranties enforceable", "the owner maintenance items that quietly void coverage when they're skipped"),
 'CapEx / Construction': ("our inspection and documentation standards one-pager", "the report format, photo record and closeout package we run under portfolio agreements"),
 'VP / Director Operations': ("the one-pager on keeping manufacturer roof warranties enforceable", "the owner maintenance items that quietly void coverage when they're skipped"),
 'Regional / Portfolio': ("the fall roof and exterior checklist we run with regional teams", "what our inspectors actually find this time of year"),
 'Procurement / Risk': ("a real bid leveling where the low number turned out to be the most expensive offer on the table", "three exterior proposals leveled against one owner scope"),
 'Site level': ("the one-pager on keeping manufacturer roof warranties enforceable", "the owner maintenance items that quietly void coverage when they're skipped"),
}
GIVE2_SEGMENT = {
 'Senior living': ("the one-pager on keeping manufacturer roof warranties enforceable on occupied campuses", "the owner maintenance items that quietly void coverage"),
 'Student housing': ("the one-pager on keeping manufacturer roof warranties enforceable", "the owner maintenance items that void coverage, which matter double on hard-used student roofs"),
 'HOA / Condo': ("the fall roof and exterior checklist, the version managers hand to boards", "what our inspectors find on association buildings each fall"),
}

PAST_EMPLOYER = [
 ("I saw you were at [CLIENT] before {company}. We've handled the roofing and exterior work for them the last few years, so there's a decent chance we were on the same properties without knowing it.",
  "Did you ever work with anyone from Hustad while you were there?"),
 ("Small world. We've been doing the roof and exterior work for [CLIENT] the last few years, and I noticed you spent time there before {company}.",
  "Did you ever cross paths with any of our crews while you were at [CLIENT]?"),
 ("Noticed [CLIENT] in your background. We've handled their roofing and exterior for the last few years and still do, so we may have been on the same buildings at some point.",
  "Did you ever work with anyone from Hustad while you were there?"),
]
SHORT_BODY = {
 'Ownership / Executive': "We handle roofing and exterior for owners and operators, mostly the visibility work: what's fine, what needs watching, what's headed for capital.",
 'Asset management': "We handle the roof and exterior side for portfolios like that one, mostly condition reads and the repair versus capital call before budgets get set.",
 'Facilities / Maintenance': "We handle roofing and exterior: scheduled inspections, leak and storm response, and small repairs done on the same visit.",
 'CapEx / Construction': "We handle capital roof and exterior work on occupied properties, from the condition read and scope through the work itself.",
 'VP / Director Operations': "We handle roofing and exterior across portfolios, one inspection standard and one report format everywhere.",
 'Regional / Portfolio': "We handle roofing and exterior on occupied properties: inspections, service, storm response, and capital roof work.",
 'Procurement / Risk': "We run roof and exterior programs under portfolio agreements, with one reporting standard and a pre-approved cap on small repairs.",
 'Site level': "We handle roofing and exterior: inspections, leak calls, storm response, and the bigger roof projects.",
}

# ---------------------------------------------------------------------------
# Helpers and QA
# ---------------------------------------------------------------------------
def wc(s):
    return len(re.findall(r"[A-Za-z0-9$%'’.,]+", s))

def cap_hook(h):
    h = (h or '').strip().rstrip('.').strip()
    if not h: return ''
    return h[0].upper() + h[1:] + '.'

def para(*parts):
    return "\n\n".join(p.strip() for p in parts if p and p.strip())

def pick(bank, seed, salt=''):
    h = int(hashlib.md5((str(seed) + salt).encode()).hexdigest(), 16)
    return bank[h % len(bank)]

MF_WORDS = re.compile(r'\b(units?|apartments?|multifamily|beds|homes|communities)\b', re.I)
NON_MF = {'Retail', 'Industrial', 'Commercial', 'Hospitality', 'Healthcare', 'Office'}
def hook_fits(hook, seg):
    if seg in NON_MF and MF_WORDS.search(hook or ''):
        return False
    return True

BANNED = [
 'revolutionary','best in class','best-in-class','game changer','end to end','end-to-end','guaranteed',
 'circle back','just checking in','touch base','hope this finds you','i wanted to reach out','reaching out',
 'synergy','leverage','cutting edge','world class','delve','robust','seamless','streamline','holistic',
 'elevate','unlock','empower','in today’s','in today\'s','furthermore','moreover','additionally',
 'comprehensive solution','solution provider','value proposition','partner with you','in the space',
 'excited to','thrilled','i trust this','per my last','as per','utilize','spearhead','myriad','tapestry',
 'navigate the','at the end of the day','it is worth noting','landscape','align our','drive value',
 'best regards','looking forward to hearing','i am writing to','quick question:','i noticed that you',
 'we specialize in','industry leading','one stop shop','full service solution','deep dive',
 'we do roofs, siding','we can quote anything','we just want a shot','is this not where your attention',
 'better door into your organization','just to follow up','gentle reminder','bump this','top of your inbox',
]
STALE = ['graded a to f','grade a to f','before budgets lock','so the exterior line stops surprising the budget',
         'worth 15 minutes','or is there someone on your team who owns exterior capital planning',
         "it isn't complicated, it's just consistent","interpreting somebody's handwriting"]
NEW_CONSTRUCTION = ['new construction','ground up','ground-up','groundbreak','broke ground','topping out','topped out',
                    'at turnover','warranty period','new deliveries','deliver for fall','under construction',
                    "owner's side representation",'owners side representation','pre-leasing','p3 delivery','development partner']

# The content standards guide (docs/CONTENT_STANDARDS.md) applies to "every post, graphic,
# caption, and message". The banks are clean today; this keeps them clean after edits.
GUIDE_CADENCE = re.compile(r"\\b(is|are) not [^.?!]{1,60}[.;]\\s+(It|That|They|This) (is|are)\\b")
GUIDE_CRUTCHES = ["here's the thing", 'hot take', 'unpopular opinion', 'most people miss this',
 'read that again', 'let that sink in', 'only as strong as the', 'the real question is']

def qa(msg, require_question=True, min_paras=3, company=''):
    issues = []
    if GUIDE_CADENCE.search(msg): issues.append('guide cadence: X is not Y. It is Z.')
    for _c in GUIDE_CRUTCHES:
        if _c in msg.lower(): issues.append(f'guide crutch: {_c}')
    scan = msg
    if company:                      # a company called Elevate or YES! is not a copy problem
        for tok in sorted(set(re.split(r'[^A-Za-z0-9!]+', str(company))), key=len, reverse=True):
            if len(tok) > 2 or '!' in tok: scan = scan.replace(tok, ' ')
    low = scan.lower()
    if '—' in msg or '–' in msg: issues.append('dash')
    n = wc(msg)
    if n > WORD_CEILING: issues.append(f'words {n}')
    if msg.count('?') > 1: issues.append('two questions')
    if require_question and msg.count('?') == 0: issues.append('no question')
    if '!' in scan: issues.append('exclamation')
    paras = [p for p in msg.split('\n\n') if p.strip()]
    if len(paras) < min_paras: issues.append(f'paragraphs {len(paras)}')
    if not msg.startswith('Hi '): issues.append('no greeting')
    if '\n\n' not in msg: issues.append('no blank lines')
    if not re.search(r"\b\w+'(s|t|re|ve|ll|m|d)\b", msg): issues.append('no contraction, reads stiff')
    for s in re.split(r'(?<=[.?])\s+', msg.replace('\n', ' ')):
        if wc(s) > 42: issues.append('sentence too long')
        break
    for b in BANNED:
        if b in low: issues.append(f'banned: {b}')
    for s in STALE:
        if s in low: issues.append(f'stale: {s}')
    for c in NEW_CONSTRUCTION:
        if c in low: issues.append(f'NEW CONSTRUCTION: {c}')
    if re.search(r'\d+\s*-\s*\d+', msg): issues.append('numeric range with hyphen')
    return issues

# ---------------------------------------------------------------------------
# Hand-written Touch 1s, same arc, same ceiling
# ---------------------------------------------------------------------------
OVERRIDE_LANE = {'T036': 'CapEx / Construction'}
OVERRIDE_T1 = {
 'T032': para("Hi David,",
   "Twin Cities associations carry roofs and siding as common elements, and Minnesota hail turns those into board decisions.",
   "Boards don't approve roofs, they approve documents. We photograph, grade and price every deficiency by building, fix the small ones on the same visit under a pre-approved cap, and hand the manager something a board can vote on.",
   "Want a sample of that report before budgets go to the boards?"),
 'T036': para("Hi Kirk,",
   "Your value-add buys in Dallas, Denver and College Station carry an $18.7 million capital plan, and all three sit in hail country.",
   "On the exterior portion, the low bid is rarely the cheapest by closeout when three bids get written three different ways. We write one owner scope by trade and level everything against it; that's how we run student work for Cardinal Group and Yugo.",
   "Want the leveling example where the low number ended up the most expensive offer on the table?"),
 'T166': para("Hi Scott,",
   "Your Clemson and Baton Rouge beds only give you the one window each August.",
   "Acquired student assets show up with a roof history nobody's walked. We baseline every roof on the first visit for Cardinal Group and Yugo, fix what's fixable while we're up there, and flag what has to be scheduled before next turn.",
   "Would a sample condition read from a recent acquisition be useful?"),
 'T196': para("Hi Jeff,",
   "Your Gallery and Sancerre communities sit on both Florida coasts, and the residents can't move out while roof work happens.",
   "We handle roofing and exterior for Dial Retirement Communities and Charter Senior Living. Crews stage quiet, work around residents and staff, and small items get fixed on the inspection visit instead of a second mobilization.",
   "Want a sample findings report? No meeting required."),
 'T199': para("Hi Michael,",
   "CRC just added 14 shopping centers and two million square feet across seven states, on top of 10,000 apartments.",
   "Carriers keep asking for current roof condition at renewal, and almost nobody can produce it building by building. Under portfolio agreements we run one report format, photo records per building, itemized closeouts, and a not-to-exceed on small repairs so they don't come back as change orders.",
   "Want our standards one-pager to hold up against what you require now?"),
 'T052': para("Hi Tony,",
   "With SRG now part of Milhaus and the platform aiming at 100,000 units in 24 months, a lot of roofs are about to change hands.",
   "The calls that repeat are the ones where the first visit was a patch and the record was a photo on somebody's phone. We document and price every deficiency and fix the small ones on the spot under a cap you approve first; that's the program we run for Asset Living.",
   "Want a sample of that report before winter?"),
 'T093': para("Hi Zach,",
   "We're Omaha neighbors, and Goldenrod's owned book runs office, healthcare, hospitality and mixed use across five states, which is about as many roof types as one portfolio can carry.",
   "On a mixed book the exterior line is rarely one problem. It's forty small ones and two big ones, and telling them apart is the whole job. We put a condition grade and a budget range on every building.",
   "Worth a look, or is there a better person on your team for it?"),
 'T143': para("Hi Benjamin,",
   "We're Omaha neighbors. On the underwriting side, the roof line is usually the softest number in the model, carried as age plus whatever the last invoice was.",
   "We give underwriting a current condition read per building, remaining life, and a budget range, so the exterior number holds up when the committee pushes on it.",
   "Want a sample of what that read looks like on the next deal you're working?"),
}

ACQ_TITLE = re.compile(r'acquisition|diligence|transactions?|investments?\b', re.I)

# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------
def build(plan_csv, research_json, out_csv):
    plan = pd.read_csv(plan_csv)
    research = {c['company']: c for c in json.load(open(research_json))}
    rows = []

    plan = plan.copy()
    plan['_sortkey'] = plan['touch1_date'].astype(str).replace('nan', '9999-99-99')
    plan = plan.sort_values(['_sortkey', 'day_seq'], na_position='last').reset_index(drop=True)
    plan['_dayorder'] = plan.groupby('touch1_date').cumcount()

    company_seen = {}
    day_hooks, company_hooks = {}, {}
    fam_mid, fam_ask = {}, {}
    def fam(c): return ' '.join(str(c).lower().replace(',', ' ').split()[:2])
    day_mid, day_ask, day_gives, day_tail = {}, {}, {}, {}

    GLOBAL_CAP = 8
    global_use = {}
    MIDSENT = ('{give} your way', '{give} to hold', '{give} in front')
    def fit(tmpl, give):
        g = give
        if any(m in tmpl for m in MIDSENT) and ',' in give:
            g = give.split(',')[0].strip()
        return tmpl.format(give=g)
    def fresh(bank, used_day, used_co=None, seed=None, salt='', fmt=None, in_order=False, tails=None):
        """First unused variant from the bank; day-unique, family-unique, and capped plan-wide."""
        start = 0 if in_order else int(hashlib.md5((str(seed) + salt).encode()).hexdigest(), 16) % len(bank)
        best = None; firm_ok = None
        for k in range(len(bank)):
            cand = bank[(start + k) % len(bank)]
            txt = fmt(cand) if fmt else cand
            co_clash = used_co is not None and txt in used_co
            if not co_clash and firm_ok is None: firm_ok = txt
            if txt in used_day or co_clash: continue
            tail = re.split(r'(?<=[.?])\s+', txt.strip())[-1]
            if tails is not None and tail in tails and best is None:
                best = txt; continue
            if best is None: best = txt
            if global_use.get(txt, 0) < GLOBAL_CAP and (tails is None or tail not in tails):
                return txt
        # nothing clean: repeating inside a day is invisible to recipients, repeating inside a
        # firm is not, so give up day uniqueness before firm uniqueness.
        if best is not None: return best
        if firm_ok is not None: return firm_ok
        return fmt(bank[start]) if fmt else bank[start]

    for _, r in plan.iterrows():
        first = r['first_name_clean'] if isinstance(r['first_name_clean'], str) and r['first_name_clean'].strip() else str(r['First Name']).split()[0]
        company = r['Company']
        lane = OVERRIDE_LANE.get(r['target_id'], r['outreach_lane'])
        seg = r['segment']
        seed = r['url_key']
        hook, why_now, overlap = HOOKS.get(company, ("", "Budget season", "No verified company research"))
        proof = CLEARED_PROOF.get(seg, 'Asset Living')
        dkey = str(r['touch1_date'])

        # ---- opener
        f_co = fam(company)
        n_at = company_seen.get(f_co, 0); company_seen[f_co] = n_at + 1
        raw = hook if n_at == 0 else (HOOK_ALT.get(company, '') if n_at == 1 else '')
        if not hook_fits(raw, seg): raw = ''
        fb = FALLBACK_HOOK.get(seg, []) + FALLBACK_LANE.get(lane, FALLBACK_LANE['Site level'])
        # Keyed by family, not by the exact string: Homes of America and Homes of America LLC are
        # colleagues who will compare DMs, whatever their LinkedIn spelling says.
        used_h = day_hooks.setdefault(dkey, set()); used_c = company_hooks.setdefault(fam(company), set())
        h = cap_hook(raw)
        used_c_norm = {x.strip().lower() for x in used_c}
        used_h_norm = {x.strip().lower() for x in used_h}
        if not h or h.strip().lower() in used_h_norm or h.strip().lower() in used_c_norm:
            h = ''
            for k in range(len(fb)):
                cand = fb[(n_at + k) % len(fb)]
                cn = cand.strip().lower()
                if cn not in used_h_norm and cn not in used_c_norm:
                    h = cand; break
            if not h:
                for k in range(len(fb)):
                    cand = fb[(n_at + k) % len(fb)]
                    if cand.strip().lower() not in used_c_norm:
                        h = cand; break
            if not h:
                for cand in fb:
                    if cand.strip().lower() not in used_c_norm:
                        h = cand; break
            if not h:
                h = fb[n_at % len(fb)]
        used_h.add(h); used_c.add(h)

        # ---- give (role stack; acquisitions titles get the condition read)
        gvars, basis = GIVE_SEGMENT.get(seg, GIVE.get(lane, GIVE['Site level']))
        if ACQ_TITLE.search(str(r['Position'])) and 'operations' not in str(r['Position']).lower():
            gvars, basis = GIVE_ACQ
        gv_used = day_gives.setdefault(dkey, set())
        give = fresh(gvars, gv_used, seed=seed, salt='gv')
        gv_used.add(give)

        # ---- substance
        mid_used = day_mid.setdefault(dkey, set())
        fmid = fam_mid.setdefault(fam(company), set())
        fask = fam_ask.setdefault(fam(company), set())
        young = company in YOUNG_BOOK
        bank = (MEANING_SEGMENT.get(seg, []) + MEANING_LANE.get(lane, MEANING_LANE['Site level']))
        if young:
            bank = YOUNG_MEANING + [b for b in bank if 'winter' not in b and 'walked' not in b and 'closer to capital' not in b]
        def render_m(m):
            if '{proof}' in m:
                return m.format(proof=proof) if proof else None
            return m
        mbank = [x for x in (render_m(m) for m in bank) if x]
        meaning = fresh(mbank, mid_used, used_co=fmid, seed=seed, salt='mean', in_order=young)

        # ---- shape
        ask_used = day_ask.setdefault(dkey, set())
        tail_used = day_tail.setdefault(dkey, set())
        roll = int(hashlib.md5((str(seed) + 'shape').encode()).hexdigest(), 16) % 20
        # With no verified company fact the honest play is the Play 12 budget question, which needs
        # no research and is the right question in September. Researched rows keep the normal mix.
        if not raw and lane in BRIDGE_LANES and roll >= 7 and roll < 17:
            roll = roll % 7
        days_conn = int(r['days_since_connected']) if pd.notna(r['days_since_connected']) else 999
        conn = pick(next(t for lim, t in CONN_LINE if days_conn <= lim), seed, 'conn')

        def mk_bridge(q, g):
            return para(f"Hi {first},", h, q, g)
        def mk_bridge_open(q, g):          # no company fact: lead on the question itself
            return para(f"Hi {first},", q, meaning, g)
        def mk_give(m, a):
            return para(f"Hi {first},", h, m, a)
        def mk_conn(m, a):
            body2 = (conn + ' ' + h).strip() if h else conn
            mm = m if h else (IDENTITY + ' ' + m)
            return para(f"Hi {first},", body2, mm, a)
        def mk_fork(m, a):
            return para(f"Hi {first},", h, m, a)

        if roll < 7 and lane in BRIDGE_LANES:
            qbank = BRIDGE_Q_CAPEX if lane == 'CapEx / Construction' else BRIDGE_Q
            asktxt = fresh(BRIDGE_GIVE, ask_used, used_co=fask, seed=seed, salt='bg', fmt=lambda a: fit(a, give), tails=tail_used)
            abank_use = [a.format(give=give) for a in BRIDGE_GIVE]
            if raw:                                   # we have a verified fact: it opens, question follows
                midtxt = fresh(qbank, mid_used, used_co=fmid | used_c, seed=seed, salt='bq')
                used_c.add(midtxt)
                maker, mbank_use = mk_bridge, qbank
            elif any(x not in used_h and x not in used_c and x not in fmid for x in qbank):
                # no fact: the question opens, and it is the honest lead. Only while the bank
                # actually has something fresh; a repeated question is worse than a role truth.
                q = fresh(qbank, used_h, used_co=used_c | fmid, seed=seed, salt='bq')
                used_h.discard(h); used_c.discard(h)  # the role truth moves to the middle, free it up
                h = q; used_h.add(q); used_c.add(q); fmid.add(q)
                midtxt = meaning
                maker, mbank_use = (lambda m, a: para(f"Hi {first},", q, m, a)), mbank
            else:                                     # bridge bank spent for today: normal give shape
                midtxt = meaning
                asktxt = fresh(ASKS, ask_used, used_co=fask, seed=seed, salt='ask', fmt=lambda a: fit(a, give), tails=tail_used)
                maker, mbank_use, abank_use = mk_give, mbank, [a.format(give=give) for a in ASKS]
        elif roll == 19 and lane in ('Ownership / Executive', 'VP / Director Operations', 'Regional / Portfolio') and RESOURCE_ASK not in ask_used:
            midtxt, asktxt = RESOURCE_BODY[0], RESOURCE_ASK
            maker, mbank_use, abank_use = mk_give, RESOURCE_BODY, [RESOURCE_ASK]
        elif roll == 18 and lane in ('Facilities / Maintenance', 'Regional / Portfolio', 'VP / Director Operations', 'Site level'):
            midtxt = meaning
            asktxt = fresh(FORK_ASKS, ask_used, used_co=fask, seed=seed, salt='fork', tails=tail_used)
            maker, mbank_use, abank_use = mk_fork, mbank, list(FORK_ASKS)
        elif roll in (14, 15, 16):
            midtxt = meaning
            asktxt = fresh(ASKS, ask_used, used_co=fask, seed=seed, salt='ask2', fmt=lambda a: fit(a, give), tails=tail_used)
            maker, mbank_use, abank_use = mk_conn, mbank, [a.format(give=give) for a in ASKS]
        else:
            midtxt = meaning
            abank = ASKS + (ASKS_REPORT_ONLY if re.search(r'report|one-pager|summary|view|read', give) else [])
            asktxt = fresh(abank, ask_used, used_co=fask, seed=seed, salt='ask', fmt=lambda a: fit(a, give), tails=tail_used)
            maker, mbank_use, abank_use = mk_give, mbank, [a.format(give=give) for a in abank]
        m1 = maker(midtxt, asktxt)

        # ---- trim to the ceiling, keeping the shape; then fix stiffness the same way
        def candidates():
            mlist = mbank_use if young else sorted(mbank_use, key=wc)
            for m in mlist:
                for a in sorted(abank_use, key=wc):
                    if m != midtxt and (m in mid_used or m in fmid): continue
                    if a != asktxt and (a in ask_used or a in fask): continue
                    yield m, a
        if wc(m1) > WORD_CEILING and '. ' in h:
            h = re.split(r'(?<=[.?])\s+', h)[0]
            m1 = maker(midtxt, asktxt)
        if wc(m1) > WORD_CEILING:
            for m, a in candidates():
                cand = maker(m, a)
                if wc(cand) <= WORD_CEILING:
                    m1, midtxt, asktxt = cand, m, a; break
        if 'no contraction, reads stiff' in qa(m1, company=company):
            for m, a in candidates():
                cand = maker(m, a)
                if 'no contraction, reads stiff' not in qa(cand) and wc(cand) <= WORD_CEILING:
                    m1, midtxt, asktxt = cand, m, a; break
        _stmt = h.rstrip().endswith('?')          # opener is the question, so the ask must not be
        _askbank = BRIDGE_GIVE if _stmt else ASKS
        if wc(m1) > WORD_CEILING or 'no contraction, reads stiff' in qa(m1, company=company):
            gshort = give.split(',')[0].split(':')[0].strip()
            pool = [(m, a.format(give=g)) for m in sorted(mbank, key=wc) for a in _askbank for g in (give, gshort)]
            for m, a in pool:
                if (m in mid_used and m != midtxt) or (a in ask_used and a != asktxt): continue
                cand = mk_give(m, a)
                if wc(cand) <= WORD_CEILING and 'no contraction, reads stiff' not in qa(cand, company=company):
                    m1, midtxt, asktxt = cand, m, a; break
        if wc(m1) > WORD_CEILING:      # last resort: shortest legal give-shape, repeats allowed
            gshort = give.split(',')[0].split(':')[0].strip()
            m = sorted(mbank, key=wc)[0]
            a = sorted((x.format(give=gshort) for x in _askbank), key=wc)[0]
            m1, midtxt, asktxt = mk_give(m, a), m, a
        if 'two questions' in qa(m1, company=company):
            for a in BRIDGE_GIVE:
                atxt = a.format(give=give)
                cand = maker(midtxt, atxt) if maker is not mk_give else mk_give(midtxt, atxt)
                if 'two questions' not in qa(cand, company=company) and wc(cand) <= WORD_CEILING:
                    m1, asktxt = cand, atxt; break
        if r['target_id'] in OVERRIDE_T1:
            m1 = OVERRIDE_T1[r['target_id']]
        else:
            mid_used.add(midtxt); ask_used.add(asktxt)
            fmid.add(midtxt); fask.add(asktxt)
            tail_used.add(re.split(r'(?<=[.?])\s+', asktxt.strip())[-1])
            global_use[midtxt] = global_use.get(midtxt, 0) + 1
            global_use[asktxt] = global_use.get(asktxt, 0) + 1

        # ---- Touch 2: a different give than Touch 1, so the follow-up is a second gift, not a rename
        g2, b2 = GIVE2.get(lane, GIVE2['Site level'])
        if seg in GIVE2_SEGMENT: g2, b2 = GIVE2_SEGMENT[seg]
        m2 = para(f"Hi {first},",
                  f"{pick(T2_OPEN, seed, 't2o')} I can send you {g2}.",
                  pick(T2_MID, seed, 't2m').format(basis=b2),
                  pick(T2_CLOSE, seed, 't2c'))

        # ---- Touch 3
        topic = TOPIC.get(lane, TOPIC['Site level'])
        anchor = 'budgets get set'
        if seg == 'Senior living': anchor = 'winter'
        elif seg == 'Student housing': anchor = 'the post-turn window closes'
        elif seg == 'HOA / Condo': anchor = 'budgets go to the boards'
        m3 = para(f"Hi {first},",
                  f"{pick(T3_OPEN, seed, 't3o')} If a 15 minute call on {topic} would be useful before {anchor}, I'll work around your schedule.",
                  pick(T3_TAIL, seed, 't3t'))

        # ---- shared-history opener
        pe_body, pe_close = pick(PAST_EMPLOYER, seed, 'pe')
        clean_company = re.split(r'\s*[–—]\s*', str(company))[0].strip()
        m4 = para(f"Hi {first},",
                  pe_body.format(company=clean_company),
                  pe_close)

        res = research.get(company, {})
        rows.append({**{k: v for k, v in r.to_dict().items() if k not in ('_dayorder', '_sortkey')},
            'first_name_used': first,
            'company_hook': hook, 'why_now': why_now + ('; ' + overlap if overlap else ''),
            'overlap_note': overlap,
            'research_confidence': res.get('confidence', 'none'),
            'company_hq': res.get('hq', ''), 'company_type': res.get('company_type', ''),
            'company_scale': res.get('scale', ''), 'company_markets': res.get('markets', ''),
            'exterior_relevance': res.get('exterior_relevance', ''),
            'recent_news': ' | '.join(f"{n.get('date')}: {n.get('item')}" for n in (res.get('recent_news') or [])[:3]),
            'sources': ' | '.join(res.get('sources') or []),
            'touch1_dm': m1, 'touch1_words': wc(m1), 'touch1_qa': '; '.join(qa(m1, company=company)) or 'PASS',
            'touch2_dm': m2, 'touch2_words': wc(m2), 'touch2_qa': '; '.join(qa(m2, company=company)) or 'PASS',
            'touch3_dm': m3, 'touch3_words': wc(m3), 'touch3_qa': '; '.join(qa(m3, require_question=False, min_paras=3, company=company)) or 'PASS',
            'past_employer_dm': m4, 'past_employer_words': wc(m4),
            'past_employer_qa': '; '.join(qa(m4, company=company)) or 'PASS',
            'proof_used': proof, 'give_offered': give,
        })
    out = pd.DataFrame(rows)
    out.to_csv(out_csv, index=False)
    return out

if __name__ == '__main__':
    out = build(paths.s(paths.PLAN_TARGETS),
                paths.s(paths.research('companies_research.json')),
                paths.s(paths.WORK / 'plan_with_copy.csv'))
    print(out[['touch1_words', 'touch2_words', 'touch3_words', 'past_employer_words']].describe().round(1).to_string())
    for c in ['touch1_qa', 'touch2_qa', 'touch3_qa', 'past_employer_qa']:
        print('\n', c); print(out[c].value_counts().head(8).to_string())
