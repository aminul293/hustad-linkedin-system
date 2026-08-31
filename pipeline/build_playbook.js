const fs = require('fs');
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell, WidthType, AlignmentType,
  ShadingType, BorderStyle, PageBreak, TableOfContents, Header, Footer, PageNumber, LevelFormat, PositionalTab
} = require('docx');

const C = JSON.parse(fs.readFileSync('/home/claude/outreach/build/doc_content.json', 'utf8'));
const NAVY = '1F3A5F', COPPER = 'B7791F', GREY = '555555', LIGHT = 'F4F7FA', STEEL = 'D9E2EC';
const FONT = 'Arial';

const P = (text, opts = {}) => new Paragraph({
  spacing: { after: opts.after ?? 120, before: opts.before ?? 0 },
  alignment: opts.align,
  children: (Array.isArray(text) ? text : [text]).map(t => typeof t === 'string'
    ? new TextRun({ text: t, font: FONT, size: opts.size ?? 21, bold: opts.bold, italics: opts.italics, color: opts.color })
    : t),
});
const B = (text) => new TextRun({ text, font: FONT, size: 21, bold: true });
const I = (text) => new TextRun({ text, font: FONT, size: 21, italics: true, color: GREY });
const H1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { before: 360, after: 160 }, children: [new TextRun({ text: t, font: FONT, size: 30, bold: true, color: NAVY })] });
const H2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 280, after: 120 }, children: [new TextRun({ text: t, font: FONT, size: 25, bold: true, color: NAVY })] });
const H3 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_3, spacing: { before: 200, after: 80 }, children: [new TextRun({ text: t, font: FONT, size: 22, bold: true, color: COPPER })] });
const Quote = (t) => new Paragraph({ spacing: { after: 140 }, indent: { left: 480, right: 480 }, shading: { type: ShadingType.CLEAR, fill: LIGHT, color: 'auto' },
  border: { left: { style: BorderStyle.SINGLE, size: 12, color: COPPER, space: 8 } },
  children: [new TextRun({ text: t, font: FONT, size: 20 })] });
const Bullet = (t) => new Paragraph({ numbering: { reference: 'bullets', level: 0 }, spacing: { after: 60 }, children: [new TextRun({ text: t, font: FONT, size: 21 })] });
const PB = () => new Paragraph({ children: [new PageBreak()] });

function cell(text, w, opts = {}) {
  return new TableCell({
    width: { size: w, type: WidthType.DXA },
    shading: opts.fill ? { type: ShadingType.CLEAR, fill: opts.fill, color: 'auto' } : undefined,
    margins: { top: 60, bottom: 60, left: 90, right: 90 },
    children: (Array.isArray(text) ? text : [text]).map(t => new Paragraph({ spacing: { after: 40 }, children: [new TextRun({ text: String(t ?? ''), font: FONT, size: opts.size ?? 18, bold: opts.bold, color: opts.color })] })),
  });
}
function table(headers, rows, widths) {
  const total = widths.reduce((a, b) => a + b, 0);
  return new Table({
    width: { size: total, type: WidthType.DXA }, columnWidths: widths,
    rows: [
      new TableRow({ tableHeader: true, children: headers.map((h, i) => cell(h, widths[i], { fill: NAVY, color: 'FFFFFF', bold: true })) }),
      ...rows.map((r, ri) => new TableRow({ children: r.map((v, i) => cell(v, widths[i], { fill: ri % 2 ? LIGHT : undefined })) })),
    ],
  });
}
const kv = (rows) => table(['Item', 'Detail'], rows, [2600, 6760]);

const S = C.stats;
const doc = [];

// ---------------------------------------------------------------- Cover
doc.push(P('HUSTAD COMPANIES', { size: 20, bold: true, color: COPPER, after: 60 }));
doc.push(P('LinkedIn New Business Track', { size: 44, bold: true, color: NAVY, after: 60 }));
doc.push(P('Baseline, Messaging System, Reply Engine and Four Week Execution Plan', { size: 26, color: GREY, after: 300 }));
doc.push(P('Playbook v1.5  ·  August 27, 2026  ·  Built from the LinkedIn data export of August 25, 2026 and the 2026 opportunity list of August 26, 2026', { size: 20, color: GREY, after: 120 }));
doc.push(P('Companion files: Hustad_LinkedIn_NewBusiness_Baseline_v1_1.xlsx (single source of truth), Hustad_Fall_Roof_and_Exterior_Checklist_v1.docx (give), Hustad_Roof_Warranty_OnePager_v1.docx (give), and the rebuild scripts.', { size: 20, color: GREY, after: 400 }));
doc.push(P([B('What this is. '), 'The operating brain for cold, new business outreach through LinkedIn direct messages, run by Eric Caturia in one protected hour each weekday, 11:05 to 12:05 Central. It compiles the entire first degree network into one baseline, selects the highest value cold targets, gives every one of them three written touches ready to paste, and supplies the reply engine that turns answers into qualified conversations, meetings for the sales team, and referrals. It implements the Sales Brain Operating System v8 and the Buyer Psychology and Messaging Playbook v1.0, and it records one governance change, DR-3, for Eric to confirm. Version 1.5 raises the program to 40 first touches a weekday, because a network of 4,839 connections worked ten a day takes two years and worked forty takes about seven weeks. It also collapses the console and the morning verification desk into one page, so the outreach hour has a single bookmark, and adds the Outreach Desk as the mechanism that makes volume and personalisation coexist: the plan supplies a safe generic opener for every target, and the desk replaces as many of those as it can each morning with something researched, plus a storm trigger wherever a market actually took weather.'], { after: 200 }));
doc.push(P([B('Assumptions made because the answers were not yet in hand. '), 'Every contact whose current company appears on the 2026 opportunity list is excluded and routed to the account manager; Greystar stays eligible as new business. All four segments are in scope, ranked by fit. Meetings route by segment and service line through an editable table. Volume runs at the maximum the hour can carry with pre written copy. Each is easy to change in the workbook.'], { after: 200 }));
doc.push(P('Confidential. Internal use only.', { size: 18, color: GREY, italics: true }));
doc.push(PB());

// ---------------------------------------------------------------- TOC
doc.push(P('Contents', { size: 28, bold: true, color: NAVY, after: 120 }));
for (const t of ['Part A. Executive Summary', 'Part B. The Network Baseline', 'Part C. Understanding Hustad for Outreach', 'Part D. The Messaging System', 'Part E. The Reply Engine and Buyer Brain', 'Part F. Execution: The Daily Plan', 'Part G. Automation: What Is Running', 'Appendix. Open Questions for Eric']) doc.push(P(t, { after: 80 }));
doc.push(PB());

// ---------------------------------------------------------------- Part A
doc.push(H1('Part A. Executive Summary'));
doc.push(P('The network is large, young and concentrated in exactly the buyers Hustad serves. Of 4,839 connections, 4,663 have never exchanged a message with Eric, which makes this a cold outreach program by definition. About 3,600 of them fit the ideal customer profile after removing staff, active accounts, warm and hot conversations, vendors and junior roles, and 740 of those score as Tier 1 priority: portfolio level decision makers at owner operators, third party managers and association managers in multifamily, student, senior living, commercial and HOA.'));
doc.push(P('The baseline that matters most is the reply rate on Eric\'s own history: the templated "good to connect, glad to be a resource" opener was sent 98 times and drew 7 replies, about 7 percent, and almost all of those were a thank you. The messages that produced emails, redirects and meetings were the ones that named a specific, verifiable thing about the reader, translated it into a consequence, and asked one small binary question. That is the pattern this program industrializes.'));
doc.push(H3('What was built'));
doc.push(kv([
  ['Baseline workbook', 'Every connection scored and tiered; engagement state from messages, invitations and endorsements; 132 target companies researched with sources; the 2026 opportunity list applied as a live active account conflict check; a past employer check; suppression list; metrics; monthly refresh SOP.'],
  ['Target set', `${C.stats.primaries} primary cold targets at 40 a weekday, across ${C.stats.companies} companies, capped at three per firm (more only at the largest platforms) so no organization is blasted, and never two people from one firm on the same day. Six primaries at active accounts came out under Gate G2 and ${C.stats.removed_development} more because their role is purely ground up development, which Hustad does not do. The Change Log tab records every move.`],
  ['Copy', `${C.stats.messages} messages: a personalized first touch for every target, plus value follow ups and close the loops for the primaries, and a shared history opener held in reserve for each person. Median first touch ${C.stats.median_words} words against a ${C.stats.word_ceiling} word ceiling, one question each, no dashes, real paragraph breaks, every company fact traced to a source, ${C.stats.qa_failures} QA failures.`],
  ['Reply engine', 'Twenty reply categories with detection cues, action, response copy and handoff; seven decision styles and six buyer states with response modifiers and worked examples; qualification questions; meeting set scripts; referral asks; objection library.'],
  ['Execution', 'A four week calendar with a minute by minute block, priority rules, Labor Day handled, and the Friday review that gates the next increment.'],
  ['Automation', 'A compliant roadmap: automate everything except the send. Drafting, classification, research, QA, logging, reply drafting, invites and CRM sync are automated or semi automated; LinkedIn platform actions never are.'],
]));
doc.push(H3('Expected results at target rates'));
doc.push(P('At the 20 percent reply target on 160 first touches, expect about 32 replies over the three weeks, of which roughly a third convert to a meeting or a single property inspection, so 10 to 12 qualified conversations for the sales team, plus redirects to the right internal owner that become new rows for the next cycle. Reserves and the reply engine\'s referral paths add to that. Week 1 is the baseline week; the Friday review tells you whether the copy is landing before Week 2 commits more volume.'));

// ---------------------------------------------------------------- Part B
doc.push(H1('Part B. The Network Baseline'));
doc.push(H2('B1. What the export contains'));
doc.push(P('The August 25, 2026 export holds 4,869 connection rows; 30 are LinkedIn\'s blank private rows and are dropped, leaving 4,839 unique profiles across 2,075 companies. The account is young: connections start in June 2025 and 4,054 of them were made in 2026, at a pace of roughly 400 to 600 per month. Only 57 profiles shared an email address. Invitations show 4,677 outgoing requests since February 2026 of which 2,918 are now connections, an acceptance rate above 60 percent, with 1,759 still pending. Sixty one inbound invitations arrived, mostly from vendors and recruiters.'));
doc.push(table(['Measure', 'Count'], [
  ['Connections (unique, after blank rows removed)', String(S.total)],
  ['Cold: no interaction of any kind', String(S.engagement['COLD: no interaction'])],
  ['Cold: they invited Eric, no messages', String(S.engagement['COLD: they invited Eric, no messages'])],
  ['Warm: Eric messaged, no reply', String(S.engagement['WARM: Eric messaged, no reply'])],
  ['Warm: they messaged Eric or endorsed him', String(S.engagement['WARM: they messaged Eric'] + 1)],
  ['Hot: two way conversation', String(S.engagement['HOT: two-way conversation'])],
  ['Unique companies', String(S.unique_companies)],
  ['Connected in the last 45 days (eligible only)', String(S.recent_45)],
], [6400, 2960]));
doc.push(H2('B2. Who is in the network'));
doc.push(P('By seniority the network is a portfolio operations network: 1,179 regional and portfolio managers, 1,112 site managers, 887 directors, 470 vice presidents, 425 owners, presidents and principals, 228 EVPs and SVPs, 212 regional and area vice presidents and 51 asset managers. By function, 3,585 sit in operations or property management, 234 in asset management and investments, 188 in construction and capital projects, 148 in facilities and maintenance, and 33 in procurement and risk. By segment, 3,238 are conventional multifamily, 295 student housing, 259 commercial, 129 HOA and condo, 64 senior living, with smaller pockets in single family rental, retail, affordable, hospitality and military housing.'));
doc.push(P('The largest employers in the network are Greystar (222), RPM Living (164), Asset Living (110), Avenue5 (78), Cushman & Wakefield (72), Willow Bridge (51), Cardinal Group (49), ZRS (41), Pegasus (38), Scion (34), Bozzuto (32), RangeWater (31), Hawthorne (30), FirstService Residential (30) and CBRE (28). Four of those fifteen are known Hustad accounts and are excluded from cold sequences under Gate G2.'));
doc.push(H2('B3. What the message history teaches'));
doc.push(P('Eric started 157 distinct conversations. The templated opener, in four variants that all end with "glad to be a resource anytime", went to 98 people and produced 7 replies; the replies were polite acknowledgments, one redirect (a Greystar contact pointing to a colleague) and one client thank you. Passive availability does not earn a reply.'));
doc.push(P('The messages that worked shared four traits. They referenced something specific and real: an Arkansas market post, a Tacoma vendor-list post, an Austin vendor-list post, a national MSA post, each written by the person being messaged, days before. They stated one concrete capability in the reader\'s terms. They asked one small, answerable question, usually "what is the best way to get on your list". And they were sent when the reader had just signaled a need. Three of those four produced an email address and a live conversation on the first reply. The two Interface conference asks produced replies and a redirect because they carried a real event, a named colleague and a 15 minute ask.'));
doc.push(P('The cold program cannot wait for posts, so it manufactures the same specificity from research: a verified fact about the company, a consequence in the reader\'s role, one give, one question. Timing is supplied by the calendar: budget season, the post turn window, peak hurricane season, winter prep and association budget adoption all fall inside the four weeks.'));
doc.push(H2('B4. Data model and gates'));
doc.push(P('Every connection carries an engagement state, a role class (seniority and function), an outreach lane, a company class, a segment, an ICP score from 0 to 100, a tier and a program status with a reason. Statuses follow the Spine gates. G1 provenance: every row comes from the official export. G2 active account conflict: the 2026 opportunity list (1,217 opportunities across 110 CRM companies, January 2 to August 26, 2026) was matched to the LinkedIn company names in the export; every contact whose current company matches is excluded and routed to the account manager shown on the opportunity list. The workbook re-checks this live against the Client Match List tab, so adding a name there updates every row. Four probable matches are held for verification rather than excluded (Capstone Communities against Capstone On-Campus Management, CENTURION Property Group, Forward Property Management Solutions, Legacy and Lamb name matches). G3 verification: the export is dated August 25, 2026, so every title and company is inside the 183 day window; the pre send check re-confirms it on the profile. G4 caps and suppression: per person, at most two touches in seven days and one in 48 hours; a reply halts the sequence; not interested means permanent suppression.'));
doc.push(table(['Status', 'Count', 'Meaning'], [
  ['ELIGIBLE', String(S.status.ELIGIBLE), 'Cold, fits the profile, passes every gate'],
  ['HOLD', String(S.status.HOLD), 'Company unclassified, junior or unclear role, function outside the exterior decision path, CRE services firm needing role verification, or a possible active account match awaiting verification (10 rows). Verify before use.'],
  ['EXCLUDE', String(S.status.EXCLUDE), 'Active account on the 2026 opportunity list or an MSA reference (362 rows at 45 LinkedIn company names), vendor or non fit (195), warm (111), hot (29), Hustad staff (15)'],
], [1800, 1000, 6560]));
doc.push(H2('B5. Scoring, tiers and lanes'));
doc.push(P('The score rewards the people who actually own exterior decisions. Seniority contributes up to 40 points (owner, president, principal, EVP and SVP highest; site managers low), function up to 30 (facilities, construction and capital, asset management and procurement highest; leasing, HR and finance near zero), segment up to 12 (multifamily, student and senior living highest), company class up to 12 (owner operators and managers over CRE services), scale up to 8 (national platforms), and recency up to 4 (connected in the last 14 days). Tier 1 is 88 and above and never a site level role; Tier 2 is 76 to 87; Tier 3 is 60 to 75; Tier 4 is site level or below 60. Among eligible rows: 758 Tier 1, 1,465 Tier 2, 527 Tier 3, 934 Tier 4.'));
doc.push(P('Lanes decide which copy stack a person receives: Ownership and Executive, VP and Director Operations, Asset management, CapEx and Construction, Facilities and Maintenance, Regional and Portfolio, Procurement and Risk, and Site level. Segment decides the consequence line and the proof reference.'));
doc.push(H2('B6. How the 214 targets were chosen'));
doc.push(P(`Selection ran in three passes over eligible rows sorted by tier, score and recency. First, lane minimums so the plan is not all executives: 26 facilities and maintenance leaders, 26 construction and capital leaders, 26 asset managers, 44 operations VPs and directors, 12 regionals, 3 procurement and risk, and at least 55 ownership and executive contacts capped at 70. Second, segment minimums: 14 student housing, 12 senior living, 14 commercial and retail, 8 HOA and condo, 6 specialty residential. Third, fill by rank. Company caps hold at three per company, four at RPM Living, Avenue5, Greystar and Willow Bridge, and never two people at the same company on the same day. After Gate G2 removals and the removal of ground up development roles, the plan stands at ${C.stats.primaries} primaries and ${C.stats.reserves} reserves across ${C.stats.companies} companies, all Tier 1 except a handful of Tier 2 rows admitted by quota.`));
doc.push(P('Because the export carries no employment history for connections, past employment overlap is captured at the company and market level in the Overlap Note column: shared client history in the same segment, Hustad\'s Omaha base (Goldenrod, Redwood Living, Edward Rose, the Brookfield SWI venture), Wisconsin roots (Continental Properties in Menomonee Falls), the South Austin partners (Kairoi, CAF, Portico, Madera, Wilson Capital, Palladius, ResProp, Dinerstein, Up Campus), the 2026 occupied replacement in the Tacoma area (Meritus, Bozzuto\'s new Pacific Northwest units, Thrive), and the Offutt Air Force Base work for Burlington Capital (Hunt Military Communities, WinnCompanies). Person level overlap is confirmed at the pre send profile check and noted on the row.'));

doc.push(H2('B7. Active accounts applied on August 26 and the past employer check'));
doc.push(P('The opportunity export is the definitive conflict list: warm and active outreach runs through the account managers, not this program. Applying it removed six scheduled primaries (three at University Partners, and one each at Landmark Properties, DP Management and Palladius Capital Management) and every reserve at those companies; six reserves were promoted into the vacated send slots on the same dates, and six new reserves were added from already researched companies. The largest active accounts by 2026 value are listed below; the full list with account managers, states, products and stages is on the Client Accounts tab.'));
doc.push(table(['CRM account', 'LinkedIn names matched', 'Account manager(s)', '2026 opps', '2026 value', 'States'], C.active_top.slice(0, 20), [2000, 2300, 1900, 800, 1100, 1260]));
doc.push(P('Past employer at an active account. The LinkedIn export carries current company and title only; it has no employment history, and no compliant tool can read a profile\'s Experience section in bulk. The check therefore lives in the twenty second pre send routine: open the profile, open Experience, and if any past employer appears on the Client Match List, type it into the Past Employer column on the Send Queue. The row flags itself and the Shared History Opener column hands over a different first message, already written, ending with \'Did you ever work with anyone from Hustad while you were there?\' Eric sends it himself. Nothing is handed to anyone else at Hustad; the relationship belongs to the person who opened it. The same rule applies when a reply reveals the history (reply category R21). That is the honest limit of the data, and it is also the highest value use of the twenty seconds: a former Cardinal or Asset Living regional who now runs a portfolio elsewhere is the warmest cold contact in the network.'));

// ---------------------------------------------------------------- Part C
doc.push(PB());
doc.push(H1('Part C. Understanding Hustad for Outreach'));
doc.push(H2('C1. The posture'));
doc.push(P('Hustad does not go to market as a roofing contractor. The posture in every project document is a national exterior asset and risk partner for occupied portfolios: inspections, warranty compliance, storm response, service and CapEx execution in one operating relationship, with documentation discipline as the product. The Sales Brain says it plainly: the product is visibility, control, documentation, response speed, warranty credibility and capital clarity. In a DM that means Eric never opens with what Hustad does; he opens with what the reader is carrying.'));
doc.push(H2('C2. The offer set and where each fits a cold conversation'));
doc.push(table(['Program', 'What it is', 'Who it is for in this plan', 'Cleared for DMs'], [
  ['Proactive Roof Program (MSA, NTE)', 'Annual, biannual or quarterly inspections scheduled by climate region; every roof photographed, graded A to F, deficiencies priced; small items repaired in the same visit under a pre approved annual cap (a cap, not a bill); portal with status, history, storm alerts and CapEx exports; monthly, quarterly and annual reporting.', 'Every lane. It is the core story for operations, facilities, regional and executive contacts.', 'Yes. The mechanics, the A to F grade, the cap language and the KPIs are in the external decks.'],
  ['Service and storm response', 'Leak response in 24 to 72 hours by program tier, storm tracking with alerts, documented claim support and restoration.', 'Facilities, regional, risk. Any active leak reply (R12).', 'Yes for response and documentation. Never claim outcomes or coverage.'],
  ['Capital replacements', 'Roof, siding, windows, gutters and downspouts on occupied sites; daily photo logs; 98.3 percent on time completion; 2.4 day median punch list closeout.', 'CapEx, construction, asset management, ownership.', 'Yes.'],
  ['Scope Certainty', 'Fixed fee preconstruction package: one walk, bid ready scope by trade to CSI MasterFormat, Class 1 budget from Hustad unit costs, phased plan, bid form and leveling matrix. Owner keeps the deliverable and controls the bid list.', 'CapEx and construction leads; anyone who says "we bid everything".', 'Yes as a program description and the leveling example. No fees in DMs.'],
  ['Construction Management (owner representation)', 'Fee based owner\'s representative on exterior packages awarded to other contractors: buyout, field verification, pay application and change order review, schedule, closeout. Hustad does not bid the projects it manages.', 'Developers and development executives (Goldenrod, Wilson Capital, Faros, Maslow\'s, Shadowbrook, Jefferson, Oakwood).', 'Yes as a description. No fees in DMs.'],
  ['Capital Certainty (budget lock)', 'Nine month locked pricing carried through budget approval with a capped materials collar.', 'Not used in this program.', 'No. Business draft pending counsel. Never mention in a DM.'],
], [2000, 3400, 2200, 1760]));
doc.push(H2('C3. Proof bank'));
doc.push(table(['Proof', 'Wording to use', 'Status'], [
  ['Portfolio KPIs', 'Inspection to proposal 1.7 days; on time completion 98.3 percent; punch list closeout 2.4 days; leak response 24 to 72 hours by program. Rolling 12 month medians, portfolio wide.', 'Cleared (external decks)'],
  ['Proactive versus reactive economics', 'Firestone and ProLogis study: $0.14 versus $0.25 per square foot per year; 21 versus 13 year average life. NRCA case: $9.15 versus $21.23 per square foot by year 25. DoD UFC 3-110-03 on maintenance extending life.', 'Cleared (Maintenance Extends Useful Life sheet). Use one number at most per message.'],
  ['Named client references', 'Asset Living (Stacey Lecocke, EVP), Cardinal Group (senior leadership), Campus Life and Style (Santiago Quiroz Jr, SVP), Dial Retirement Communities (Ted Lowndes, President), Burlington Capital (Dominic Vaccaro, President, Offutt AFB).', 'Cleared (deck testimonials). Yugo, Core Spaces, Scion, Charter and others were named by Eric in a March 2026 DM; the copy uses Yugo and Charter sparingly and Eric can swap them out in one place in copy_engine.py.'],
  ['Bid leveling example', 'Bidder A led by $67,000 as bid and finished $41,000 above the true low after leveling; all three leveled totals within 5 percent of the estimate.', 'Cleared (Scope Certainty deck).'],
  ['Yugo program patterns', '$646,770 of priced repairs created 2022 to 2025 never approved before the next inspection replaced them; unapproved findings rewritten at 111 to 207 percent; completed work followed by 93 percent less need per square foot; 1 in 3 sub $20K recommendations dies unapproved at a median of 376 days.', 'Not cleared. Client confidential. Requires Eric\'s approval to use anonymized ("on one 81 site student portfolio"). Kept out of all DMs in this plan.'],
  ['Warranty facts', 'Coverage is limited to defined defects and approved workmanship; non leaking deficiencies are owner maintenance; documented inspections and completed maintenance keep coverage in force.', 'Cleared as general statements. Never promise coverage on a specific property.'],
], [2000, 5000, 2360]));
doc.push(H2('C4. How each project asset is used'));
doc.push(table(['Asset', 'Use in this program'], [
  ['Sales Brain Operating System v8', 'Source of truth for voice, buyer states, decision styles, role stacks, asset class playbooks, trust boundaries and objection answers. The reply engine is its application.'],
  ['Buyer Psychology and Messaging Playbook v1.0', 'The arc in 90 words, the twelve plays, the do not send list and the ten point QA. Every first touch here follows Play 7\'s shape (thin history, binary easy reply) with a research hook in place of shared history; Touch 2 is Play 5; Touch 3 is Play 6 with the referral exit.'],
  ['Project Instructions v1.1', 'Hard rules: no LinkedIn automation, human send, permanent suppression, gates, no trust boundary items, no dashes, why now on every touch.'],
  ['One Hour Daily Schedule v1.0', 'The block structure and the Friday five numbers. Adapted for higher volume in Part F.'],
  ['National Exterior Partner intro deck', 'The R10 "send me info" asset and the source of KPIs and testimonials.'],
  ['Proactive Roof Programs deck', 'Program mechanics, warranty slides (the warranty one pager give), the NOI funnel, the pilot timeline offered on calls.'],
  ['Scope Certainty deck', 'CapEx lane copy and the leveling example give.'],
  ['Construction Management deck', 'Developer copy and the owner representation angle.'],
  ['MSA template and exhibits', 'What a program conversation leads to: preferred vendor agreement, portfolio schedule, scope of work with NTE limits, last look language, dedicated account manager and portal logins. Used on calls, not in DMs.'],
  ['Yugo mid year report, NTE recommendations and property briefs', 'The format of the one page capital view, the two page property summary and the findings report gives, after redaction and approval. Also the internal evidence for the approval mortality story.'],
  ['Capital Certainty one pager and FAQ', 'Internal only until counsel clearance. Not used.'],
  ['Maintenance Extends Useful Life', 'The one cleared economics citation.'],
], [2800, 6560]));

// ---------------------------------------------------------------- Part D
doc.push(PB());
doc.push(H1('Part D. The Messaging System'));
doc.push(H2('D1. Why this copy should clear 20 percent'));
doc.push(P('Every message runs the Sales Brain arc compressed into a DM: open on their reality (a verified company fact, or the honest thin-history line about when we connected), one piece of evidence translated into that role\'s consequence, then the path, which is always a give from the role stack (the capital view sample for owners, the two page summary for asset managers, the checklist for operations, the leveling example for construction, the standards one pager for procurement), and one small ask with the exit open. The first ask is the give, never a meeting; the meeting is Touch 3\'s job. About a third of the plan runs the Play 12 budget season bridge: when next year\'s exterior numbers get built, is there a current condition read behind them, or is it mostly age and invoices. The rules underneath: it has to read like Eric typed it, contractions and plain words, a hard ceiling of 90 words with a median near 78, exactly one question, no dashes, no links, no hype vocabulary. No two people on one send day share an opening line, a middle, or a closing ask, and no two people at the same company family ever open on the same sentence. Companies whose operating book is young and self built get a documentation and warranty upkeep story, because an aging roof story would tell them we do not know their portfolio.'));
doc.push(P('The ask sizes follow the Playbook\'s role stacks: executives get the one page capital view or a 15 minute look; asset managers get the two page property summary; facilities and regional leaders get the findings report or the fall checklist; construction leads get the leveling example or a scope conversation; risk and procurement get the standards one pager. Segment consequence lines and proof names come from the Playbook\'s crosswalk: student housing turn windows with Cardinal Group and Yugo, senior living quiet execution with Dial and Charter, military housing with Burlington Capital at Offutt, HOA boards and reserve studies, retail work windows, build to rent per building roofs.'));
doc.push(H2('D2. The three touch sequence'));
doc.push(table(['Touch', 'Day', 'Purpose', 'Shape', 'Words'], [
  ['1. First DM', 'Day 0', 'Earn a reply with a give, not a meeting ask', 'Their reality, evidence with role meaning, the give, one small ask with the exit open', '54 to 90'],
  ['2. Value follow', 'Day 7 (next business day)', 'A give, not a nudge; CTA is accepting the give', 'Play 5: a give rather than a nudge, the give, what it is built from, and an easy yes', 'about 66'],
  ['3. Close the loop', 'Day 14 (next business day)', 'Small CTA, autonomy preserved, referral exit, then cooldown', 'Play 6: last note, a short call on one specific topic before a real anchor, and a name is plenty if it is not their desk', 'about 51'],
], [1500, 1500, 2600, 2900, 860]));
doc.push(P('A reply at any touch halts the rest. Quiet after Touch 3 means a 120 day cooldown and a note. Touch 2 and 3 are deliberately templated by lane and segment so Eric can send them fast; the personalization budget goes into Touch 1, which is where reply rate is decided.'));
doc.push(H2('D3. Worked examples from the plan'));
for (const e of C.examples) {
  doc.push(H3(`${e.name}, ${e.position}, ${e.company}  (${e.lane}; ${e.segment}; ${e.words} words)`));
  doc.push(P([I('Why now: ' + e.why_now)], { after: 60 }));
  doc.push(Quote('Touch 1: ' + e.t1));
  doc.push(Quote('Touch 2: ' + e.t2));
  doc.push(Quote('Touch 3: ' + e.t3));
  if (e.shared_history) doc.push(Quote('If a past employer turns out to be a Hustad client, this replaces Touch 1: ' + e.shared_history));
}
doc.push(H2('D4. Pre send QA (every message, every day)'));
doc.push(P('The workbook already linted every message for length, dashes, exclamation marks, double questions, hyphenated numeric ranges, banned vocabulary, missing paragraph breaks, stiff phrasing with no contraction, phrases that were overused in the previous version, and any language that implies ground up construction. The human check before each send takes 20 seconds: open the profile from the row; confirm the title and company still match; confirm no reply has arrived on an earlier touch; confirm the company is not on Client Accounts or Suppression; read the Experience section, and if a past employer is on the Client Match List switch to the Shared History Opener and put that company where [CLIENT] sits; read the hook once more and ask whether Eric could say the why now line out loud; paste; send; mark Sent with the time. If anything fails, skip the row and pull the next reserve.'));

// ---------------------------------------------------------------- Part E
doc.push(PB());
doc.push(H1('Part E. The Reply Engine and Buyer Brain'));
doc.push(P('A reply is a person, not a row. Every reply halts the sequence, gets a same day answer inside the block, and is logged with its category, the style and state read, the response sent, the next step, its date and the Hustad owner. The engine below covers the twenty reply shapes that account for nearly everything a cold DM produces. Slots in braces are filled from the row and the reply; the voice never changes.'));
doc.push(H2('E1. Reply triage: twenty categories'));
for (const r of C.replies) {
  doc.push(H3(`${r.id}. ${r.category}`));
  doc.push(P([B('Cues: '), r.cues], { after: 60 }));
  doc.push(P([B('Action: '), r.action], { after: 60 }));
  doc.push(Quote(r.response));
  if (r.response_to_referred) doc.push(Quote('To the referred person: ' + r.response_to_referred));
  doc.push(P([B('Next and log: '), r.next, '  ', B('Handoff: '), r.handoff], { after: 140 }));
}
doc.push(H2('E2. Reading decision style from a reply'));
doc.push(P('Style is observable, never assumed. On the first reply, classify from the tells below, apply the modifier to the next message, and record it in the Reply Log so every later message and the meeting brief carry it. When two styles show, the one attached to the question they actually asked wins.'));
doc.push(table(['Style', 'Tells in the reply', 'Modifier', 'Example response'], C.styles.map(s => [s.style, s.tells, s.modifier, s.example]), [1500, 2400, 2400, 3060]));
doc.push(H2('E3. Reading buyer state'));
doc.push(table(['State', 'Cues', 'Adjustment'], C.states.map(s => [s.state, s.cues, s.adjust]), [1900, 3700, 3760]));
doc.push(H2('E4. Qualification in a DM conversation'));
doc.push(P('Ask one question per message, in whatever order the conversation allows, and never all of them. Three answered questions are enough to route a meeting; the rest belong on the call.'));
doc.push(table(['Field', 'Question', 'Why'], C.qual.map(q => [q.field, q.question, q.why]), [1800, 4400, 3160]));
doc.push(H2('E5. Setting the meeting and handing it off'));
doc.push(table(['Moment', 'Copy'], Object.entries(C.meeting).map(([k, v]) => [k.replace(/_/g, ' '), v]), [1800, 7560]));
doc.push(P('Routing (editable in the workbook):', { bold: true, after: 60 }));
doc.push(table(['Trigger', 'Owner', 'Backup'], C.handoff.map(h => [h.trigger, h.owner, h.backup]), [3600, 3600, 2160]));
doc.push(H2('E6. Referral asks'));
doc.push(table(['When', 'Copy'], C.referrals.map(r => [r.when, r.copy]), [2800, 6560]));
doc.push(H2('E7. Objection library'));
doc.push(table(['They ask', 'Plain answer'], C.objections.map(o => [o.q, o.a]), [2800, 6560]));

// ---------------------------------------------------------------- Part F
doc.push(PB());
doc.push(H1('Part F. Execution: The Daily Plan'));
doc.push(H2('F1. Decision Record DR-3: volume for the new business track'));
doc.push(P('The warm program\'s charter set a ceiling of five touches per day for a small warm market. Eric\'s instruction for this track is maximum cold volume per session with copy ready to paste. DR-3 therefore sets the new business track at the volume one hour can carry with pre written copy: Week 1 ramps first touches at 15, 20, 25, 25 and 15 while replies are still few; Weeks 2 and 3 add 30 new targets each plus the scheduled follow ups; Week 4 is follow ups only and the monthly refresh. Total planned sends are 480 across five calendar weeks, with daily totals between 8 and 40 and the last thirty close the loop messages spilling into the first week of October. The per person caps, the reply halt, permanent suppression and the human send rule are unchanged. If Eric prefers the original ceiling, the Send Queue can be cut to five rows per day without changing anything else.'));
doc.push(P('LinkedIn safety note: there is no published daily limit for messages to first degree connections, and every message here is different and relevant, which is what LinkedIn\'s spam signals look for. Keep sends spaced a minute or two apart, stop the day if LinkedIn shows any warning, and never send identical text to more than one person in a day.'));
doc.push(H2('F2. The calendar'));
doc.push(table(['Week', 'Dates', 'New first touches', 'Follow ups', 'Notes'], [
  ['1', 'Aug 31 to Sep 4', '100 (15, 20, 25, 25, 15)', 'none', 'Baseline week. Friday review decides Week 2 volume.'],
  ['2', 'Sep 8 to 11 (Labor Day Sep 7 has no sends)', '30 (8, 8, 8, 6)', 'Touch 2 for Week 1: 28, 32, 25, 15', 'Heaviest paste days. Follow ups first, then new.'],
  ['3', 'Sep 14 to 18', '30 (8, 6, 6, 6, 4)', 'Touch 2 for Week 2 (0, 8, 8, 8, 6) and Touch 3 for Week 1 (0, 28, 32, 25, 15)', 'Replies accumulate; expect 6 to 10 open conversations.'],
  ['4', 'Sep 21 to 25', '0', 'Touch 2 for Week 3 (8, 6, 6, 6, 4) and Touch 3 for Week 2 (0, 8, 8, 8, 6)', 'Close the cycle, run the gate review, request the October export.'],
  ['5 (spillover)', 'Sep 28 to Oct 2', '0, or the October cycle begins', 'Touch 3 for Week 3 (8, 6, 6, 6, 4)', 'Light week; overlaps the monthly refresh.'],
], [700, 2200, 2000, 2800, 1660]));
doc.push(H2('F3. The block, minute by minute'));
doc.push(table(['Time', 'Monday', 'Tuesday to Thursday', 'Friday'], [
  ['11:05 to 11:12', 'Reply sweep: LinkedIn inbox and the Reply Log. Categorize each reply with the engine.', 'Reply sweep and categorize.', 'Reply sweep and categorize.'],
  ['11:12 to 11:22', 'Conflict refresh: re-check today\'s queue against Client Accounts and Suppression; backfill any skipped row from Reserve.', 'Reply handling: answer every reply with the engine copy, log it, route handoffs. A reply outranks any send.', 'Reply handling.'],
  ['11:22 to 11:35', 'Follow ups: Touch 2 then Touch 3 from the queue, 30 to 45 seconds each.', 'Follow ups: Touch 2 then Touch 3.', 'Follow ups.'],
  ['11:35 to 12:00', 'New first touches: open profile, 20 second check, paste, send, mark Sent. 60 to 90 seconds each.', 'New first touches.', '11:35 to 11:52 weekly review: fill Metrics, process opt outs, note blocked rows, read the replies again for style and state patterns.'],
  ['12:00 to 12:05', 'Log anything unlogged. Glance at tomorrow\'s queue.', 'Log. Tee up tomorrow.', 'Tee up Monday; request the export if it is the last Friday of the month.'],
], [1400, 2700, 2700, 2560]));
doc.push(P('Priority rule when the hour is short: replies, then Touch 2, then Touch 3, then new first touches. Skipped new touches roll to the next day; skipped follow ups do not roll more than one day. If the queue exceeds 30 sends, defer new first touches rather than compressing the reply time.'));
doc.push(H2('F4. Metrics and the Friday review'));
doc.push(P('Five numbers every Friday, from the Metrics tab: first touches sent versus plan; reply rate on first touches; positive reply rate; meetings set and referrals received; compliance count, which must read zero. Targets: reply rate 20 percent or better, positive replies 10 percent or better, one meeting or single property inspection for every three replies. Week 1 is diagnostic. If reply rate is under 12 percent after Week 1, do not add volume; instead review the twenty lowest performing messages by lane, tighten hooks, and re-test on Week 2\'s thirty new targets before committing Week 3.'));
doc.push(H2('F5. Monthly refresh'));
doc.push(P('On the first business day of each month, request a fresh export, run the classifier, diff against the prior month on profile URL, write Move, Role change, New connection and Removal events, suppress removals, re-verify anyone whose title or company changed, and rebuild the next cycle\'s target set excluding everyone already touched, suppressed, or replied within 90 days. A Move or role change at a fitting account is the highest openness moment the data can detect and jumps to Band A. The full SOP and the scripts are in the workbook\'s Refresh SOP tab.'));

// ---------------------------------------------------------------- Part G
doc.push(PB());
doc.push(H1('Part G. Automation: What Is Running'));
doc.push(P('The hard rule is fixed and it shapes everything else: nothing acts on LinkedIn except Eric\'s hands. No auto connect, no auto message, no scraping, no browser bots, no third party LinkedIn tools. Everything around the send is now automated, and four scheduled Claude tasks are live as of August 26, 2026. This part records what exists, what it does, what it cannot do yet, and the one request to IT that removes the last manual step.'));
doc.push(H2('G1. What the connector can and cannot do'));
doc.push(P('The Microsoft 365 connector was tested against Eric\'s tenant on August 26. Reading works and writing does not. Graph returned FORBIDDEN on both write paths, naming the delegated permissions that are missing admin consent. This is a tenant configuration matter, not a design choice, and the program was built around it rather than waiting on it.'));
doc.push(table(['Capability', 'Status', 'What it means for the program'], [
  ['Read OneDrive and SharePoint files', 'Works', 'Every task reads the send queue, the roster, the client match list, the suppression list and the reply engine straight from the LinkedIn folder.'],
  ['Read Outlook mail', 'Works', 'The reply desk finds LinkedIn message notifications in the inbox and reads the message text out of them. Verified: notifications arrive from messaging-digest-noreply, hit-reply, invitations and notifications-noreply at linkedin.com.'],
  ['Write files to OneDrive', 'Blocked. Files.ReadWrite.All is not admin consented.', 'Tasks cannot write the logs back. Instead each task publishes a private page on claude.ai and hands Eric a ready made log line to paste.'],
  ['Send mail from the mailbox', 'Blocked. Mail.Send is not admin consented.', 'Tasks cannot email the console or the digest. They notify through Claude instead, by push and by the task summary email.'],
], [2100, 2700, 4560]));
doc.push(P('The IT request, in one line: grant admin consent for the delegated permissions Files.ReadWrite.All and Mail.Send on the Microsoft 365 connector application, client id api://07c030f6-5743-41b7-ba00-0a6e85f37c17, tenant 1c056d9d-dbb7-4901-a367-f7370b0058d9. Nothing else about the program changes when that lands; the tasks simply start writing the logs themselves and the console can arrive as an email.'));
doc.push(H2('G2. The folder'));
doc.push(P('OneDrive, LinkedIn, LinkedIn New Business Track. Flat, no subfolders, file names exact, because the tasks look files up by name. It holds the send queue files (one per send day), the reserves file, the roster, the client match list, the 2026 active account summary, the reply engine, the program status note, the log templates, and the working scripts themselves (classify, hooks, copy engine, calendar, console builder), so the monthly refresh session can rebuild everything from the folder alone. README_FIRST.md in the folder repeats all of this for whoever opens it next.'));
doc.push(H2('G3. The four scheduled tasks'));
doc.push(P('Each one starts a fresh Claude session, does its work, publishes to a fixed page so Eric keeps one bookmark per job, and notifies him. All four carry the same guardrails in their instructions: never act on LinkedIn, never invent a contact or a fact, never put pricing, warranty, claim or deductible language in a draft, no dashes, ninety word ceiling, one question per message.'));
doc.push(table(['Task', 'Runs', 'What it does', 'Where it lands'], [
  ['Morning Brief', 'Weekdays 10:45 Central, twenty minutes before the block', 'Reads the standing console page and its embedded log, cross checks today\'s companies against the client match list and suppression, and sends a short brief: counts by touch, anything to skip and why, replied halts, and yesterday\'s completion. It does not rebuild the console; the page manages itself.', 'A plain notification with the console link. Push and email.'],
  ['Reply Desk', 'Weekdays at 8:30, 10:30, 13:30 and 16:30 Central', 'Searches the inbox for LinkedIn message notifications since the last sweep, reads the full message text, matches the sender against the roster, classifies the reply against the twenty one categories, reads decision style and buyer state, and drafts the answer with every slot filled. Silent when there is nothing new.', 'The page titled Hustad Reply Desk. Push and email notification when there are replies.'],
  ['Friday Review', 'Fridays 12:10 Central', 'Computes the five numbers with the arithmetic shown, breaks reply rate down by lane and segment, quotes the three weakest and three strongest performers, recommends next week\'s volume, names which reserves to promote, and on the last Friday of the month asks for the export.', 'The page titled Hustad Weekly Review. Email notification.'],
  ['Monthly Refresh', 'First of the month, 6:00 Central', 'Looks for a new LinkedIn export and a new CRM opportunity export. If they are absent it says so and stops. If present it runs the whole rebuild: diff on profile URL, engagement state, active account gate, scoring, pinned reselection, and it lists every Move and Role change as Band A. It rebuilds the console page with the new plan while preserving the embedded send log, and delivers the regenerated CSVs as files.', 'The page titled Hustad Monthly Refresh, plus the new files delivered in the session. Email notification.'],
], [1500, 1700, 4400, 1760]));
doc.push(P('Two scheduling notes. The cron schedules are stored in UTC and were set against Central Daylight Time; when Chicago moves to standard time on November 1, 2026, every task fires one hour earlier in local terms until the schedules are shifted. And the reply desk depends on LinkedIn message notification emails still arriving, which stops if Eric reads a message in the LinkedIn app before the sweep runs; in that case he pastes the reply text into the project and gets the same classification and draft on demand.'));
doc.push(H2('G4. What stays manual, and why'));
doc.push(table(['Step', 'Reason'], [
  ['Requesting the LinkedIn export', 'LinkedIn issues it only to the logged in account holder. The Friday review removes the forgetting, not the click.'],
  ['Sending every message', 'The Project Instructions and LinkedIn\'s terms both prohibit automation on the platform. The console reduces the send to a paste.'],
  ['The twenty second profile check, including Experience', 'No compliant tool reads profiles in bulk. This is where the past employer flag and the title change are caught, and it is the highest value human step in the program.'],
  ['Dropping send_log.csv into the folder now and then', 'The console logs every tick into itself and hands back the file on demand; the OneDrive copy is the archive. Reply log lines still paste, tab separated so they land in columns.'],
  ['Approving anything that reaches a client', 'Human approval rule for external communication until the workflow is proven.'],
  ['Deciding weekly volume and the verify matches', 'Judgment calls the metrics inform but do not make.'],
], [3200, 6160]));
doc.push(H2('G5. What to do first'));
doc.push(P('One drag and drop. Unzip Hustad_LinkedIn_OneDrive_Bundle_v1_1.zip and drop all thirty four files into OneDrive, LinkedIn, LinkedIn New Business Track. That is the only setup step; the tasks are already scheduled and will find their files there on Monday morning. Then send IT the one line permission request in G1. Everything else runs on its own.'));

// ---------------------------------------------------------------- Appendix
doc.push(PB());
doc.push(H1('Appendix. Open Questions for Eric'));
doc.push(table(['Question', 'Default in this build', 'Change by'], [
  ['Confirm DR-3 volume or revert to five per day', 'DR-3 volume as planned', 'Cutting the Send Queue to five rows per day'],
  ['Verify four probable active account matches', 'Held, not messaged: Capstone Communities, CENTURION Property Group, Forward Property Management Solutions, Legacy (two names) and Lamb Communities', 'Mark ACTIVE or remove on the Client Match List'],
  ['Past employer rule', 'Settled August 26: Eric sends the shared history opener himself and keeps the conversation. Nothing routes internally', 'Already applied in R21, the Send Queue and the console'],
  ['Segment priorities', 'All four, ranked by fit, with quotas', 'Editing quotas in select_targets.py and rerunning'],
  ['Handoff owners', 'Routing table in Part E5, now aligned to the account managers on the opportunity list', 'Editing the Handoff Routing tab'],
  ['Use of Yugo and Charter as named proof in DMs', 'Used in student and senior living copy alongside deck cleared names', 'One line change in copy_engine.py, then regenerate'],
  ['Anonymized Yugo approval mortality story', 'Not used', 'Approve, and it becomes a Touch 2 evidence line for asset and ownership lanes'],
  ['Redacted sample report, two page summary and one page capital view', 'Promised as gives; Eric produces the redactions', 'Produce before Week 2 Touch 2 dates (September 8)'],
  ['Three companies not verified by research (Sunrise Communities, Atlas Management, and any new reserve marked RESEARCH NEEDED)', 'Fallback opener without company facts; confirm on profile', 'Replace the row with a reserve if the profile does not fit'],
  ['The four scheduled tasks', 'Live as of August 26, 2026, reading the OneDrive LinkedIn folder', 'Ask to pause, retime or change any of them'],
  ['Microsoft permissions', 'Read works, write and send are blocked', 'IT grants admin consent for Files.ReadWrite.All and Mail.Send on the connector app'],
], [3400, 3200, 2760]));
doc.push(H2('Change log, v1 to v1.1'));
doc.push(table(['Target', 'Name', 'Company', 'Change', 'Reason'], C.change_log.map(r => [r.target_id, r.name, r.company, r.change, r.reason]), [900, 1900, 2200, 1900, 2460]));

// ---------------------------------------------------------------- Build
const document = new Document({
  creator: 'Hustad Companies',
  title: 'Hustad LinkedIn New Business Track Playbook v1.5',
  styles: { default: { document: { run: { font: FONT, size: 21 } } },
    paragraphStyles: [
      { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: { font: FONT, size: 30, bold: true, color: NAVY }, paragraph: { spacing: { before: 360, after: 160 }, outlineLevel: 0 } },
      { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: { font: FONT, size: 25, bold: true, color: NAVY }, paragraph: { spacing: { before: 280, after: 120 }, outlineLevel: 1 } },
      { id: 'Heading3', name: 'Heading 3', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: { font: FONT, size: 22, bold: true, color: COPPER }, paragraph: { spacing: { before: 200, after: 80 }, outlineLevel: 2 } },
    ] },
  numbering: { config: [{ reference: 'bullets', levels: [{ level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 270 } } } }] }] },
  features: { updateFields: true },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1200, bottom: 1100, left: 1300, right: 1300 } } },
    headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [new TextRun({ text: 'Hustad Companies  ·  LinkedIn New Business Track  ·  Playbook v1.5  ·  Confidential', font: FONT, size: 16, color: GREY })] })] }) },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: 'Page ', font: FONT, size: 16, color: GREY }), new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 16, color: GREY })] })] }) },
    children: doc,
  }],
});
Packer.toBuffer(document).then(buf => { fs.writeFileSync('/home/claude/outreach/out/Hustad_LinkedIn_NewBusiness_Playbook_v1_5.docx', buf); console.log('written'); });
