# -*- coding: utf-8 -*-
"""
Reply Engine and Buyer Brain content for the Hustad New Business Track (LinkedIn DMs).
Every reply template is under 90 words, one CTA, plainspoken, no dashes, no trust boundary items.
Slots in braces are filled by Eric from the row and the reply.
"""

# ---------------------------------------------------------------------------
# A. Reply triage: category -> detection cues, action, response copy, log fields
# ---------------------------------------------------------------------------
REPLY_CATEGORIES = [
 {
  'id': 'R1', 'category': 'Yes to the give (sample, checklist, example)',
  'cues': 'sure, send it, yes please, would love to see it, sounds useful, go ahead',
  'action': 'Send the give the same day (link to the cleared asset or a PDF). Then one qualifying question. Do not propose a call in the same message as the give.',
  'response': "Great, here it is: {give_link_or_attachment}. It is built from what our inspectors actually document on occupied properties, so it should read as familiar. One question so I do not waste your time later: when you look at roofs across {company_short}, is the harder part getting a straight condition read, or getting the small repairs done without a second trip?",
  'next': 'Log R1. Set follow up for +3 business days if quiet: R1b.',
  'handoff': 'None yet',
 },
 {
  'id': 'R1b', 'category': 'Give sent, then quiet for 3 business days',
  'cues': 'no reply after the give',
  'action': 'One light follow up that asks for a reaction, not a meeting.',
  'response': "Did the {give_name} land the way you expected, {first}? If one section is worth a conversation, a 15 minute call is easy to set up. If it is filed for later, that is a fine outcome too.",
  'next': 'If quiet after this, cooldown 60 days. Log.',
  'handoff': 'None',
 },
 {
  'id': 'R2', 'category': 'Open to a call',
  'cues': 'happy to chat, let us set something up, send me times, what does your calendar look like, call me',
  'action': 'Propose two windows inside 5 business days. Confirm who should join from their side. Name who joins from Hustad by segment (routing table). Book on the Hustad calendar and send a calendar invite by email the same day.',
  'response': "Great. Easiest path: {day_1} between {window_1} or {day_2} between {window_2}, 15 minutes, video or phone. I will bring {the_specific_thing_promised} so the time is useful either way, and {hustad_owner} from our team will join since they run {segment} programs day to day. Which works better, and is there anyone on your side who should be on it?",
  'next': 'Log R2. On confirmation: Outlook invite, recap note to hustad_owner with the row, the research notes, and the reply thread. Status = Meeting set.',
  'handoff': 'Route by segment and service line (see HANDOFF table)',
 },
 {
  'id': 'R3', 'category': 'Redirect: not my desk, talk to X',
  'cues': 'not my area, you want to talk to, our facilities lead handles that, reach out to',
  'action': 'Thank them. Ask for a name if not given. Message the named person within 2 business days with the referral framing. Log both rows; the original row goes to Cooldown 120 days with a note.',
  'response': "Thank you, that is exactly what I needed. I will reach out to {referred_name} and keep it short. If it is easier, feel free to forward this note and I will follow their lead on timing. Appreciate you pointing me the right way.",
  'response_to_referred': "{referred_first}, {referrer_first} suggested I reach out to you on roof and exterior programs for {company_short}. Short version: we inspect and grade every roof A to F, fix the small items in the same visit under a pre-approved cap, and give {segment_role} one page of repair versus capital before budgets lock; we run that for {proof}. Would a sample of that report be useful, or is a 15 minute call easier?",
  'next': 'Log R3 with referred name and URL. New row for the referred person: Band A, Touch 1 = referral message.',
  'handoff': 'None until the referred contact replies',
 },
 {
  'id': 'R4', 'category': 'We already have a vendor / under contract',
  'cues': 'we have a roofer, we use a national vendor, we are under contract, we have an MSA with, our current provider',
  'action': 'Never disparage the incumbent. Offer the last look or the second set of eyes on one property. Ask when the program comes up for review. Set cooldown to that date.',
  'response': "Understood, and a good incumbent is worth keeping. Where we usually earn a spot is as the second set of eyes on one property: an inspection with photos, an A to F grade and a priced list you can hand to your current vendor or to us. No commitment either way, and it gives you a benchmark for the next renewal. When does the current program come up for review?",
  'next': 'Log R4 with review date. Cooldown to 30 days before that date. If they accept the one property read, route to Nancy Ly (service) or Will Moore (portfolio).',
  'handoff': 'Nancy Ly for a single property read; Will Moore or Chad Uphoff if a portfolio review is requested',
 },
 {
  'id': 'R5', 'category': 'We handle roofs in house',
  'cues': 'our maintenance team does that, we have in house crews, we self perform',
  'action': 'Respect the team. Position the inspection format and documentation as support for the in house team, not a replacement. Offer the report format.',
  'response': "That is a real advantage, and most in house teams we work with keep the repairs. Where we add something is the documentation layer: one inspection format, an A to F grade per roof, photo records the carriers and manufacturers ask for, and a priced list your team can work from. If a sample of that report format would help your team, I will send it. No pitch attached.",
  'next': 'Log R5. If they accept the sample, follow R1. If not, cooldown 90 days.',
  'handoff': 'None',
 },
 {
  'id': 'R6', 'category': 'Not now / budgets done / next year',
  'cues': 'budgets are locked, come back in the spring, next year, bad timing, after turn, after the holidays',
  'action': 'Accept the timing exactly. Offer to leave the give in their file. Set next_due_date to their stated timing. No contact before then.',
  'response': "Understood. I will come back around {their_stated_timing}, and nothing from me before then. If it is useful to have in the file for that cycle, I can send the {give_name} now so it is there when the numbers open up. Either way, thank you for the straight answer.",
  'next': 'Log R6. Status Cooldown, next_due_date = stated timing. Honor it exactly.',
  'handoff': 'None',
 },
 {
  'id': 'R7', 'category': 'Asks what Hustad does / who are you',
  'cues': 'what exactly do you do, tell me more, who is Hustad, what do you offer',
  'action': 'Two sentences, evidence first, then one question. No capability dump.',
  'response': "Fair question. Hustad is a 50 year old roofing and exterior partner that runs inspection, repair and capital programs for occupied portfolios: multifamily, student, senior living, retail and commercial. Every roof gets photographed and graded A to F, small items are fixed in the same visit under a pre-approved cap, and ownership gets one page of repair versus capital; {proof} runs on that program. Which part of that would matter most at {company_short}, the inspection read or the same visit repairs?",
  'next': 'Log R7. Classify style from the next reply.',
  'handoff': 'None',
 },
 {
  'id': 'R8', 'category': 'Geography: do you cover X / are you licensed in X',
  'cues': 'do you work in, are you licensed in, we are in Florida, our portfolio is in',
  'action': 'Answer plainly from the license register (Eric verifies the specific state before answering). National reach, local accountability. Ask where the assets are concentrated.',
  'response': "Yes on {state_or_market}; we run programs across most of the lower 48 with onsite supervision on every job, and the reporting looks the same in every market. Where is the portfolio most concentrated? That tells me which of our regional teams should be in the conversation.",
  'next': 'Log R8. Confirm licensing for the named states in the register before sending. If a state is not covered, say so plainly and offer the nearest covered market.',
  'handoff': 'Regional BD (Jeff Knapp, Chris Pfanstiel, Mitch Brechon) by market once a call is set',
 },
 {
  'id': 'R9', 'category': 'Pricing question',
  'cues': 'what does it cost, send pricing, how much, rates',
  'action': 'No prices in DM (trust boundary). Explain how the program is structured and move to a call where scope can be sized. Never quote $/SF or caps in a DM.',
  'response': "Happy to walk through it properly rather than guess in a message. The shape is simple: inspections under a portfolio agreement are low or no cost depending on cadence and workload, repairs run against a pre-approved annual cap per property, which is a ceiling and not a bill, and anything larger is priced as its own proposal with photos behind every line. The numbers depend on roof area, slope and building count, so a 15 minute call with a property list gets you a real answer. Want to do that this week?",
  'next': 'Log R9. If they send a property list, route to Will Moore or Chad Uphoff for sizing.',
  'handoff': 'Will Moore or Chad Uphoff (national accounts) for sizing',
 },
 {
  'id': 'R10', 'category': 'Send me info / vendor packet / add you to our list',
  'cues': 'send me your info, do you have a capabilities deck, send W9 and COI, vendor registration, we use a vendor portal',
  'action': 'Send the National Exterior Partner intro deck (cleared) plus the vendor packet on request. Ask what triggers a first assignment. Register in their portal if one exists.',
  'response': "Will do. I will send our intro deck and the vendor packet (COI, W9, license list) by email so it lands in the right place; what is the best address? One question so the packet does not just sit in a folder: what usually triggers the first assignment for a new exterior vendor with you, an inspection, a leak, or a capital project?",
  'next': 'Log R10. Send packet within 1 business day. Follow up in 10 business days with a give (R1 path).',
  'handoff': 'Admin sends packet; Eric follows up',
 },
 {
  'id': 'R11', 'category': 'Curious but skeptical: how is this different / heard this before',
  'cues': 'every roofer says that, how are you different, we have been burned, what is the catch',
  'action': 'Open with what we know and what we do not know. Smallest claim in the library. Offer proof, never push it.',
  'response': "Fair. What we know: the inspection is photographed and graded the same way on every roof, small items are fixed while the crew is there instead of on a second trip, and the report is written for the person approving the money, not for the roofer. What we do not know yet is whether your roofs need any of that. The honest test is one property: if the report tells you nothing new, that is the answer. Worth one?",
  'next': 'Log R11, style = Skeptical scar tissue. If yes, route to Nancy Ly for a single property inspection.',
  'handoff': 'Nancy Ly (service and inspections)',
 },
 {
  'id': 'R12', 'category': 'Active problem: leak, storm damage, failing roof',
  'cues': 'we actually have a leak, storm came through, we have a roof failing at, active water intrusion',
  'action': 'Containment first, zero selling. Get address, contact and access. Route to Nancy Ly (service) or Ashley Walter (storm and claims) the same hour. Reply within the block.',
  'response': "Let us get eyes on it. If you send me the property address and the onsite contact, I will have our service lead {service_owner} reach out today to schedule a look and, if needed, temporary protection. No paperwork needed before we help. Is there active water inside right now?",
  'next': 'Log R12 as HOT. Text or call the routed owner immediately. Status = Active service lead.',
  'handoff': 'Nancy Ly (leaks, service). Ashley Walter (storm, insurance, large restoration).',
 },
 {
  'id': 'R13', 'category': 'Not interested',
  'cues': 'no thanks, not interested, please stop, remove me',
  'action': 'One graceful close. Suppress permanently and globally the same day. Never re-add.',
  'response': "Understood, and thanks for the straight answer. I will close the loop on my end and will not reach out again. If anything ever changes, the door is open on your side.",
  'next': 'Log R13. Suppression list, permanent. Compliance count stays at zero.',
  'handoff': 'None',
 },
 {
  'id': 'R14', 'category': 'One word or emoji acknowledgment',
  'cues': 'thanks, 👍, noted, appreciate it',
  'action': 'Treat as a door left open, not a yes. One line of value plus a binary question. Do not send the full sequence.',
  'response': "Appreciate it, {first}. Quick binary so I do not clutter your inbox: is roof and exterior something you touch at {company_short}, or is it better placed with someone else on the team?",
  'next': 'Log R14. If a name comes back, R3. If quiet after 5 business days, continue sequence at Touch 2.',
  'handoff': 'None',
 },
 {
  'id': 'R15', 'category': 'Refers you to a peer at another company',
  'cues': 'you should talk to my friend at, our sister company, my old colleague at',
  'action': 'Thank them. Ask for a two line intro or permission to use their name. Send a forwardable note.',
  'response': "That is generous, thank you. If you know {peer_name} well enough for a two line intro, I will send you a short forwardable note so it costs you thirty seconds. If it is easier, I can reach out directly and mention you pointed me their way. Which do you prefer?",
  'next': 'Log R15. New row for the peer (Band A). Send forwardable note within 1 business day.',
  'handoff': 'None',
 },
 {
  'id': 'R16', 'category': 'We only use local vendors / you are too far away',
  'cues': 'we prefer local, are you even in our area, we use local guys',
  'action': 'Agree that local accountability matters. Explain onsite supervision and regional teams. Ask where the assets are.',
  'response': "Local accountability matters, and it is how we run: a named regional team, onsite supervision on every job, and the same report in every market so a regional in Dallas and one in Charlotte read the same page. Where are your assets concentrated? If we are not the right fit for that market, I will say so.",
  'next': 'Log R16. Verify market coverage. If covered, route to regional BD.',
  'handoff': 'Regional BD by market',
 },
 {
  'id': 'R17', 'category': 'Asks for references or proof',
  'cues': 'who else do you work with, can I talk to a client, references',
  'action': 'Offer the deck testimonials (Asset Living, Cardinal Group, Campus Life and Style, Dial Retirement Communities, Burlington Capital) and a reference call we arrange directly. Do not share client data.',
  'response': "Yes. The names we can share publicly are Asset Living, Cardinal Group, Campus Life and Style, Dial Retirement Communities and Burlington Capital, and their notes are in our intro deck. For a live reference in your asset class I will set that up directly; it usually takes a few days. Which asset class matters most for the reference?",
  'next': 'Log R17. Set up the reference call yourself. Send deck.',
  'handoff': 'Account owner for the reference (Will Moore, Chad Uphoff)',
 },
 {
  'id': 'R18', 'category': 'Question about warranty, claims or insurance outcomes',
  'cues': 'will this keep our warranty valid, can you get our claim approved, what about our deductible',
  'action': 'Trust boundary. Never promise coverage, claim outcomes or deductible results. Explain documentation and route to Ashley Walter for storm and claims, or to a call.',
  'response': "I want to be careful here, because warranty and claim outcomes depend on the policy and the manufacturer terms, not on anything I can promise in a message. What we do is build the record both of them ask for: documented inspections, completed maintenance items, photo history by building, and itemized closeouts. If you want to walk through a specific situation, {storm_owner} runs our storm and claims work and can look at it with you. Want me to set that up?",
  'next': 'Log R18. Route to Ashley Walter if storm or claim related. No coverage statements in writing.',
  'handoff': 'Ashley Walter (storm restoration, insurance claims)',
 },
 {
  'id': 'R19', 'category': 'Asks for a proposal or a site visit directly',
  'cues': 'can you come look at, send a proposal for, we need a quote on',
  'action': 'Ready to move. Drop the sequence. Get address, contact, access, and the decision in front of them. Route to the service or capital owner the same day.',
  'response': "Yes. Send me the property address and the best onsite contact, and {routed_owner} will get the visit scheduled this week. Two quick things so the first visit is useful: is this a repair question, a replacement question, or a full inspection, and who needs to see the report on your side?",
  'next': 'Log R19 as Ready to move. Route same day. Status = Opportunity.',
  'handoff': 'Nancy Ly (repairs, inspections). Ashley Walter (replacements, capital, storm). Will Moore (portfolio program).',
 },
 {
  'id': 'R20', 'category': 'Hostile or spam accusation',
  'cues': 'stop spamming, how did you get my info, this is a sales pitch',
  'action': 'One sentence, no defense, suppress permanently.',
  'response': "Understood, and I apologize for the intrusion. I will not message again.",
  'next': 'Log R20. Permanent suppression. Review the draft that triggered it in the Friday review.',
  'handoff': 'None',
 },
 {
  'id': 'R21', 'category': 'They used to work at a company Hustad works for now',
  'cues': 'I used to be at Cardinal, when I was with Asset Living, we worked with you guys at my last company, your team did our roofs at X',
  'action': 'This is a gift, not a routing problem. Stay in the conversation yourself. Say plainly that we still work with that company, do not claim to remember them, and turn the shared history into a question about the work rather than about us. Never hand the person to someone else at Hustad; the relationship is yours.',
  'response': "Small world, and good to hear. We still handle {active_account}, going on a few years now. Did you ever work with anyone from our crew while you were there? Curious what your read was, because whatever you liked or did not like about how it ran is exactly what I would want to get right for {company_short}.",
  'next': 'Log R21 with the past employer named. Fill the Past Employer column on the row. Keep the sequence with you; do not pause it and do not hand it off. If their answer is positive, ask for a condition read on one property. If they never dealt with our crew, drop it and go back to the normal thread.',
  'handoff': 'None. Eric keeps this conversation.',
 },
]

# ---------------------------------------------------------------------------
# B. Decision style detection (Sales Brain v8 Section 9) applied to replies
# ---------------------------------------------------------------------------
DECISION_STYLES = [
 {'style': 'Analytical verifier', 'tells': 'Asks for definitions, backup, sample reports, what is included and excluded, how the grade is calculated, comparability across vendors. Longer messages with specific questions.',
  'modifier': 'Name the evidence basis and offer the backup: summary first, detail available. Answer the exact question asked before anything else. Never round or generalize.',
  'example': "Good question. The grade is set per roof section from documented condition and remaining useful life, not age alone, and every finding carries a photo and a price. I can send the two page summary plus the full appendix behind it so you can see how the numbers roll up. Which would you rather see first?"},
 {'style': 'Decisive controller', 'tells': 'Short replies, fast, wants the point, asks what the next step is, uses imperatives (send it, set it up, who do I talk to).',
  'modifier': 'Bottom line in sentence one. CTA carries an owner and a date. No preamble.',
  'example': "Next step: a 15 minute call with {hustad_owner} on Thursday at 10 or 2 Central. I will send the sample report before the call so it is a decision, not a demo. Which time?"},
 {'style': 'Risk shield', 'tells': 'Asks about warranties, insurance, documentation, what could go wrong, liability, who is responsible, what happens if.',
  'modifier': 'Name what is preserved: small reversible first step, options kept open, documentation as protection. No promises on outcomes.',
  'example': "The first step is reversible: one inspection with photos and a graded report. Nothing gets repaired without your approval, the cap is a ceiling not a bill, and the report is yours to keep whichever way you go. Would one property be a reasonable place to start?"},
 {'style': 'Consensus builder', 'tells': 'Mentions ownership, a committee, regionals, the VP, needs to run it by someone, asks for something to share.',
  'modifier': 'Swap the call for a forwardable one pager they can send up without translating. Offer to write the internal summary.',
  'example': "Makes sense. I will send a one page summary written for the people you need to bring along: what the program is, what it costs to start, and what changes for the site teams. If it helps, I can draft the two lines you would use to introduce it internally. Who else needs to feel comfortable before this moves?"},
 {'style': 'Operational protector', 'tells': 'Talks about site teams, residents, disruption, access, noise, leasing season, turn, staff burden.',
  'modifier': 'Name quiet execution and sequencing before anything else. Show the site team gains time, not work.',
  'example': "The sequencing comes first: inspections are scheduled with the site, crews check in with the office, work zones are set so residents keep their access, and small repairs happen while the crew is already there so the site is not chasing a second visit. The report goes to you, not to the site team to interpret. Would that fit how your properties run?"},
 {'style': 'Price led comparator', 'tells': 'Mentions bids, numbers, help me compare, what your rates are, we bid everything.',
  'modifier': 'Name scope clarity and what a low number usually excludes. Never lead with price. Offer the leveling example.',
  'example': "Comparing is the right move, and the useful comparison is scope, not the bottom line. Two roof proposals at the same price can describe different work, and the low one usually wins on what it left out. I can send a one page example of three bids leveled to one scope so you can see how that plays out. Useful?"},
 {'style': 'Skeptical scar tissue', 'tells': 'References a prior vendor failure, we have heard this before, every roofer says that, burned before.',
  'modifier': 'Open with what we know and what we do not know. Make the smallest claim in the library. Offer one property as the test.',
  'example': "Understood, and you should be skeptical. What we know is how we document and price; what we do not know is whether your roofs need any of it. One property, one inspection, one report. If it tells you nothing new, that is the answer and I will not push. Worth one?"},
]

# ---------------------------------------------------------------------------
# C. Buyer state detection (Sales Brain v8 Section 7) in replies
# ---------------------------------------------------------------------------
BUYER_STATES = [
 {'state': 'Calm evaluator', 'cues': 'Full sentences, good questions, no time panic, replies within a day or two.', 'adjust': 'Structured reply, tradeoffs allowed, can carry a slightly larger ask (a 15 minute call).'},
 {'state': 'Compressed and overloaded', 'cues': 'Short replies, long silence then a burst, asks for the bottom line, replies at odd hours.', 'adjust': 'Cut to 40 words. Bottom line first. One binary question. Separate now from later.'},
 {'state': 'Guarded and skeptical', 'cues': 'Asks what is excluded, references a prior vendor, wants proof before talk.', 'adjust': 'Lead with what we know and what we do not know yet. Offer proof, never push it. Smallest possible claim.'},
 {'state': 'Anxious and loss focused', 'cues': 'Mentions active damage, residents, premiums, a deadline.', 'adjust': 'Containment first, options second, one small reversible step. Route to a call fast. Zero selling.'},
 {'state': 'Consensus builder', 'cues': 'Mentions a regional, ownership, a committee, or needs to run it by someone.', 'adjust': 'Offer a forwardable one pager instead of a meeting. Make their internal job easy.'},
 {'state': 'Ready to move', 'cues': 'Asks for schedule, scope, or who shows up.', 'adjust': 'Drop the sequence. Be decisive: owner, date, next step. Confirm timing and remove friction.'},
]

# ---------------------------------------------------------------------------
# D. Qualification framework for DM conversations (ask no more than one per message)
# ---------------------------------------------------------------------------
QUALIFICATION = [
 {'field': 'Scope', 'question': "How many properties or units does your team cover, and in which markets?", 'why': 'Sizes the program and picks the regional team.'},
 {'field': 'Ownership of the decision', 'question': "Who owns roof and exterior decisions at {company_short}: regional ops, facilities, asset management, or ownership?", 'why': 'Multi-threading map. Names the second contact.'},
 {'field': 'Current state', 'question': "How are roof inspections handled today: a vendor program, in house walks, or mostly when something leaks?", 'why': 'Reveals reactive versus proactive and the incumbent.'},
 {'field': 'Pain', 'question': "What did the last 12 months of roof spend look like: mostly leak calls and emergency dispatches, or planned work?", 'why': 'Loss aversion framed factually; sets the value story.'},
 {'field': 'Timing', 'question': "When do next year's capital numbers lock, and is there a turn or leasing window we should plan around?", 'why': 'Sets the calendar and the why now.'},
 {'field': 'Format preference', 'question': "Would one recommendation help more, or two options with tradeoffs?", 'why': 'Playbook question; reveals decision style.'},
 {'field': 'Committee', 'question': "Who else needs to feel comfortable before a program like this moves?", 'why': 'Playbook question; reveals consensus needs.'},
]

# ---------------------------------------------------------------------------
# E. Handoff routing table (editable). Segment and service line -> Hustad owner.
# ---------------------------------------------------------------------------
HANDOFF = [
 {'trigger': 'Portfolio or MSA conversation, multi state, national operator', 'owner': 'Will Moore (national portfolio partnerships) with Chad Uphoff (Director of National Accounts)', 'backup': 'Eric Caturia'},
 {'trigger': 'Single property inspection, repairs, service cadence, in house team support', 'owner': 'Nancy Ly (National Account Manager, repairs and service)', 'backup': 'Dustin Intlekofer (Director of Service and Maintenance)'},
 {'trigger': 'Replacement, capital project, storm restoration, insurance claim', 'owner': 'Ashley Walter (National Account Manager, capital projects, storm, claims)', 'backup': 'Eric Caturia'},
 {'trigger': 'Scope Certainty (bid ready scope and leveling) or Construction Management (owner representation)', 'owner': 'Eric Caturia', 'backup': 'John Michael Measells (Principal)'},
 {'trigger': 'Regional business development, local vendor list onboarding, market specific follow up', 'owner': 'Jeff Knapp (BDM National Accounts), Christopher Pfanstiel (BDM), Mitch Brechon (BDM) by market', 'backup': 'Chad Uphoff'},
 {'trigger': 'Student housing program (turn season, campus portfolios)', 'owner': 'Will Moore with John Michael Measells (both attend Interface and student events)', 'backup': 'Chad Uphoff'},
 {'trigger': 'Senior living program', 'owner': 'Will Moore', 'backup': 'Nancy Ly'},
 {'trigger': 'Wisconsin market', 'owner': 'Ryan Bentley (General Manager, Wisconsin)', 'backup': 'Eric Caturia'},
]

# ---------------------------------------------------------------------------
# F. Meeting set mechanics, recap, and referral asks
# ---------------------------------------------------------------------------
MEETING_SET = {
 'confirm': "Locked in: {day} at {time} Central, 15 minutes, {video_or_phone}. Invite coming from my email so it lands on your calendar. {hustad_owner} will join. I will send the {give_name} the day before so we can spend the time on your properties, not on slides.",
 'internal_recap': "HANDOFF: {full_name}, {position}, {company} ({segment}). Source: LinkedIn New Business Track, Touch {n}, reply category {R_id}. Style read: {style}. State: {state}. What they said: {summary}. What they want: {ask}. Portfolio facts: {scale_markets}. Why now: {why_now}. Promised: {give}. Meeting: {date_time}. Next step owner: {owner}. Row: {target_id}.",
 'day_before': "Looking forward to tomorrow at {time}, {first}. Attached is the {give_name} I mentioned. If you have a property list or even a couple of addresses, send them over and we will come with something specific.",
 'no_show': "We missed each other today, no problem at all. I will hold {two_new_windows}; reply with whichever works, or send a time that suits you better.",
 'post_meeting': "Thanks for the time today, {first}. Summary for your file: {three_bullets_in_prose}. Next step on our side: {owner} sends {deliverable} by {date}. On your side: {their_action}. If anything in that summary is off, tell me and I will correct it.",
}

REFERRAL_ASKS = [
 {'when': 'Reply says not my desk', 'copy': "Thanks, that saves us both time. Who on the team carries roof and exterior programs, and is it all right if I mention you pointed me their way?"},
 {'when': 'After a positive meeting (asked once, in the recap or a day later)', 'copy': "One small ask, decline freely: is there someone else in your world, a peer at another operator or an owner you work with, who wrestles with the same roof problems? A two line intro is plenty and I will keep it short with them."},
 {'when': 'After delivering a give they liked', 'copy': "Glad it was useful. If a regional or an asset manager on your team would benefit from the same read, feel free to forward it, or send me a name and I will reach out directly with the same no strings offer."},
 {'when': 'They mention having worked at a company Hustad works for now', 'copy': "Since you know how we run it, is there anyone else you came up with who is dealing with the same roof headaches now? A name is plenty and I will keep it short with them."},
]

# ---------------------------------------------------------------------------
# G. Objection library (short answers for the common questions, Sales Brain Section 21)
# ---------------------------------------------------------------------------
OBJECTIONS = [
 {'q': 'Why inspect now instead of waiting?', 'a': "Because the small items are cheap now and expensive after the first freeze or the first storm. The inspection also puts a documented baseline in the file before budgets lock, which is when the roof line gets argued about."},
 {'q': 'Why fix something that is not leaking yet?', 'a': "Non leaking items like lifted seams, loose flashing and failed sealant are exactly what manufacturers classify as owner maintenance. Leave them and the warranty conversation gets harder; fix them in the inspection visit and it costs a fraction of the leak call."},
 {'q': 'How is this different from normal wear?', 'a': "Normal wear is expected and graded. What we flag is the wear that has reached the point where water follows it inside, and we show the photo so you can judge it yourself."},
 {'q': 'What is the downside of deferring to budget season?', 'a': "Deferred items get repriced, usually higher, and some of them become interior events in the meantime. The proposal expires; the problem does not."},
 {'q': 'What is included and excluded in your inspection?', 'a': "Included: every roof section photographed, graded A to F, deficiencies priced, drains and penetrations checked, warranty checkpoints logged. Excluded: destructive testing and engineering opinions, which we will tell you when a roof needs them."},
 {'q': 'What makes your bid different from the low number?', 'a': "Scope. Our proposals separate base scope, unit price items, change order triggers, warranty path and owner responsibilities so you can see what the low number left out. We are glad to be leveled against anyone on the same scope."},
 {'q': 'How do warranties work after installation?', 'a': "A system warranty covers membrane and approved workmanship; a membrane only warranty covers the material. Both require documented inspections and completed owner maintenance items to stay in force. We build that record annually. Specific coverage is always per the manufacturer's document."},
 {'q': 'What happens when reality changes in the field?', 'a': "Concealed conditions are documented with photos before anything is done, priced against the unit rates in the proposal, and approved before work continues. No surprises on the invoice."},
 {'q': 'Do you do new construction?', 'a': "No. We work on buildings that are already standing: inspections, service and maintenance, storm response, and capital roof and exterior work on occupied properties. If you are building something new, we are not your contractor, and I will say so rather than waste your time."},
 {'q': 'We already have a roofer.', 'a': "Most portfolios do, and plenty of them are fine. The question is usually whether you have a current condition read per building, or whether you have a phone number you call when something leaks. If it is the first one, you do not need us. If it is the second, that is the gap we fill."},
 {'q': 'Are you licensed where our properties are?', 'a': "Tell me the states and I will confirm before we go any further. We are not going to pretend to cover a market we cannot service properly."},
]

# ---------------------------------------------------------------------------
# H. Content engagement. The reply categories above handle answers to outreach. Since the posting
# calendar went live, a second inbound lane exists: people who engage with the content before any
# DM is sent. Those are the warmest contacts the program produces, and they arrive in public, where
# a weak reply is visible to their whole network. No templates here on purpose. A comment reply
# that could have been pasted from a library is worse than no reply.
# ---------------------------------------------------------------------------
ENGAGEMENT = [
 {'when': 'Substantive comment on our post',
  'do': 'Answer inside 90 minutes while the post is live. Agree with the specific thing they said, '
        'then add the one thing they did not have. Their comment is the setup; the value is what '
        'you know that they do not, from the exterior side.',
  'discipline': 'Never list obvious tactical items. Match their altitude: someone writing about '
                'systems gets an answer about systems. No pitch, no link, no company name unless it '
                'carries the point. Then DM the same day referencing the exchange.'},
 {'when': 'They post something in our lane and we are the guest',
  'do': 'Comment on their post, not just their comment on ours. Their audience is our audience, and '
        'contributing on their turf is worth more reach than posting our own.',
  'discipline': 'Contribute one idea, take responsibility where the vendor side owns the problem, '
                'and sell nothing. Do not mirror their sentence rhythm, especially if they write in '
                'the constructions our own standards ban.'},
 {'when': 'DM after they engaged with content',
  'do': 'Open by naming the exchange so they can place you, agree with their point, then describe '
        'how we actually run it (docs/SERVICE_DELIVERY.md), then one give. Client names carry real '
        'weight here: the cleared list is Asset Living, Cardinal Group, Campus Life and Style, '
        'Dial Retirement Communities and Burlington Capital, plus regional relationships Eric names '
        'himself.',
  'discipline': 'Longer than a cold first touch is fine when they wrote at length; matching their '
                'depth reads as respect. Still one ask, still the give first, still no pricing.'},
 {'when': 'They reshare or quote our content',
  'do': 'Thank them in the thread in one line, and look at who engaged with their reshare. A '
        'reshare puts our material in front of a network we did not have.',
  'discipline': 'No ask attached to a thank you. If someone in their network engaged too, that is a '
                'separate first touch, run through the normal gates.'},
]

# Where the give sits at that moment. Content engagement earns a different give than cold outreach:
# they have already read a point of view, so the next step is the thing behind it.
ENGAGEMENT_GIVES = [
 'The sample property record, redacted: what one building\'s documentation actually looks like.',
 'The post storm documentation sequence, one page, baseline through closeout.',
 'The Exterior Risk File newsletter, if the topic they engaged on is the month\'s theme.',
]
