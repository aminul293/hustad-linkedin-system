const fs = require('fs');
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, ShadingType, AlignmentType, LevelFormat, Footer, BorderStyle } = require('docx');
const NAVY = '1F3A5F', COPPER = 'B7791F', GREY = '555555', LIGHT = 'F4F7FA', FONT = 'Arial';

const P = (t, o = {}) => new Paragraph({ spacing: { after: o.after ?? 100, before: o.before ?? 0 }, alignment: o.align, children: [new TextRun({ text: t, font: FONT, size: o.size ?? 20, bold: o.bold, italics: o.italics, color: o.color })] });
const H = (t) => new Paragraph({ spacing: { before: 200, after: 80 }, border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: COPPER, space: 2 } }, children: [new TextRun({ text: t, font: FONT, size: 22, bold: true, color: NAVY })] });
const Bul = (t) => new Paragraph({ numbering: { reference: 'b', level: 0 }, spacing: { after: 40 }, children: [new TextRun({ text: t, font: FONT, size: 19 })] });
function cell(t, w, o = {}) { return new TableCell({ width: { size: w, type: WidthType.DXA }, shading: o.fill ? { type: ShadingType.CLEAR, fill: o.fill, color: 'auto' } : undefined, margins: { top: 50, bottom: 50, left: 80, right: 80 }, children: [new Paragraph({ children: [new TextRun({ text: t, font: FONT, size: 18, bold: o.bold, color: o.color })] })] }); }
function table(h, rows, w) { return new Table({ width: { size: w.reduce((a, b) => a + b, 0), type: WidthType.DXA }, columnWidths: w, rows: [new TableRow({ tableHeader: true, children: h.map((x, i) => cell(x, w[i], { fill: NAVY, color: 'FFFFFF', bold: true })) }), ...rows.map((r, ri) => new TableRow({ children: r.map((x, i) => cell(x, w[i], { fill: ri % 2 ? LIGHT : undefined })) }))] }); }

const common = (title, subtitle, children, file) => {
  const d = new Document({
    styles: { default: { document: { run: { font: FONT, size: 20 } } } },
    numbering: { config: [{ reference: 'b', levels: [{ level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 400, hanging: 220 } } } }] }] },
    sections: [{
      properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 900, bottom: 800, left: 1000, right: 1000 } } },
      footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: 'Hustad Companies  ·  National reach, local accountability  ·  Planning reference only, not a warranty, coverage or claim opinion for any specific property.', font: FONT, size: 15, color: GREY })] })] }) },
      children: [
        P('HUSTAD COMPANIES  ·  BUILD. PROTECT. RESTORE.', { size: 16, bold: true, color: COPPER, after: 40 }),
        P(title, { size: 32, bold: true, color: NAVY, after: 40 }),
        P(subtitle, { size: 19, color: GREY, italics: true, after: 160 }),
        ...children,
      ],
    }],
  });
  Packer.toBuffer(d).then(b => { fs.writeFileSync(file, b); console.log('written', file); });
};

// ------------------------------------------------------------------ Checklist
common('Fall Roof and Exterior Checklist', 'What our inspectors document on occupied properties before the wet season, and what site and regional teams can check themselves in twenty minutes per building.', [
  H('Before you go up: the file'),
  Bul('Roof system, age and manufacturer for each section; warranty documents located and registered; last inspection and repair records in one place.'),
  Bul('Open service tickets from the last 12 months by building: repeat addresses are the first stop.'),
  Bul('Approved repair authority for the season, so small items can be fixed on the visit instead of waiting for a second trip.'),
  H('Low slope roofs (TPO, PVC, EPDM, modified bitumen)'),
  Bul('Drains, scuppers and gutters clear of debris; standing water lines around drains; strainers in place.'),
  Bul('Seams and flashings: lifted edges, open laps, fishmouths at walls, curbs and parapets.'),
  Bul('Penetrations: pipe boots, pitch pans and sealant at HVAC curbs, vents and conduit; cracked or shrunken sealant is an owner maintenance item under most warranties.'),
  Bul('Rooftop equipment: condensate lines discharging onto the membrane, service walk pads, trades debris and screws left from HVAC work.'),
  Bul('Membrane surface: punctures, blisters, exposed scrim, ponding, granule loss on modified bitumen.'),
  H('Steep slope roofs (shingle, tile, metal)'),
  Bul('Missing, lifted or creased shingles; exposed nails; ridge and hip caps; valleys clear.'),
  Bul('Flashings at chimneys, walls and skylights; step flashing and kickout flashing present where roof meets siding.'),
  Bul('Gutters and downspouts attached, sloped and clear; splash blocks and extensions in place; ice dam history noted in cold climates.'),
  Bul('Soft metals, vents and gutters checked for hail impact after any storm; dents on soft metals are a triage sign, not a claim conclusion.'),
  H('Walls, windows and the rest of the envelope'),
  Bul('Sealant at windows, doors and dissimilar materials; weep holes clear; stucco and siding cracks and gaps; wood trim rot at ends and horizontal surfaces.'),
  Bul('Breezeways, stair towers and balconies: water staining on ceilings, deck coatings, drainage at thresholds.'),
  Bul('Interior top floor units and common areas with staining, bubbling or a prior leak ticket: walk them with the roof section above in mind.'),
  H('After a storm: what site staff should look for'),
  Bul('Leaves and debris on the ground, dents in cars and soft metals, broken windows or siding, missing shingles or shingles on the ground, downspout and gutter dents, punctures or splits in membrane, and any new water entry. These are triage signs. Photograph them with a date and the building number; the roof conclusion comes from the inspection.'),
  H('What good documentation looks like'),
  table(['Element', 'Standard'], [
    ['Photos', 'Every finding photographed with the building and roof section identified; time stamped; stored by property in one portal, not on a phone.'],
    ['Grade', 'One condition grade per roof section, A to F, tied to remaining useful life, so the replacement window is a planning number rather than a surprise.'],
    ['Priced list', 'Every deficiency priced; urgent items separated from preventive items so approvals can be made in one decision.'],
    ['Same visit repairs', 'Small items repaired under a pre approved cap while the crew is on the roof; the cap is a ceiling, not a bill; unused authorization is never invoiced.'],
    ['Closeout', 'Itemized closeout with photos of completed work; warranty checkpoints logged; open items aged and owned.'],
  ], [2200, 8040]),
  H('Segment notes'),
  P('Student housing: turn exposes every roof and gutter problem at once; schedule the inspection inside the first six weeks after move in so repairs land before winter and before the next turn is planned.', { size: 19 }),
  P('Senior living: inspections and repairs are sequenced around residents and staff; crews check in with the community office, work zones keep access clear, and noisy work is scheduled with the executive director.', { size: 19 }),
  P('Retail and commercial: off hours scheduling protects tenants; drains and HVAC penetrations are the usual sources on open air centers; tenant coordination is documented in the report.', { size: 19 }),
  P('Build to rent and single story communities: every home carries its own roof; per building inspection and per building pricing keep the exterior line predictable across hundreds of small roofs.', { size: 19 }),
  P('Industry planning context: proactive inspection and repair programs average about $0.14 per square foot per year against about $0.25 for reactive service, with average roof life of 21 years versus 13 (Firestone and ProLogis study, directional planning ranges). Outcomes on any specific property depend on system, installation, exposure and response time.', { size: 17, color: GREY, italics: true, before: 120 }),
], '/home/claude/outreach/out/Hustad_Fall_Roof_and_Exterior_Checklist_v1.docx');

// ------------------------------------------------------------------ Warranty one pager
common('Your Roof Warranty: What It Covers, and What It Expects of You', 'Plain answers to the questions owners and managers ask most, drawn from how manufacturer warranties are written. Coverage on any specific roof is always governed by that roof\'s warranty document.', [
  H('What a warranty covers'),
  Bul('Coverage is limited to defined manufacturing defects and approved workmanship items. A warranty is not a guarantee of a leak free roof in all conditions.'),
  Bul('A system warranty covers the membrane and the approved installation workmanship, issued through the manufacturer and a certified contractor, with broader coverage and longer terms.'),
  Bul('A membrane only warranty covers the roofing material against manufacturing defects. It does not include labor, flashing or workmanship items.'),
  H('What is typically excluded'),
  Bul('Damage from lack of maintenance or from other trades working on the roof.'),
  Bul('Weather events outside tested parameters.'),
  Bul('Items listed as owner maintenance.'),
  Bul('Interior damage. Warranties cover the roof assembly; interior finishes and contents are generally an insurance matter.'),
  H('Are non leaking deficiencies covered?'),
  P('Usually no. Lifted seams, loose flashing and deteriorating sealant are maintenance items. Correcting them proactively helps maintain warranty validity and keeps small items from escalating into the kind of failure the warranty then argues about.', { size: 19 }),
  H('What the owner is expected to do to keep coverage in force'),
  table(['Owner responsibility', 'What it means in practice'], [
    ['Maintain an inspection cadence', 'Documented inspections on a schedule, with photos, stored by property.'],
    ['Complete minor repairs', 'Debris removal from the surface and drains; replacement of deteriorated sealant, caulk and pitch pans; tightening or replacing exposed fasteners; cleaning gutters, scuppers and downspouts.'],
    ['Repair third party damage', 'Rooftop damage caused by other trades (HVAC, telecom, solar) is the owner\'s to fix, and to document.'],
    ['Keep records', 'Photo records and reports in a central place; manufacturer maintenance guidelines followed; warranty documents registered.'],
    ['Report promptly and use certified contractors', 'Issues reported when found; repairs performed by contractors certified for that system so the repair itself does not void coverage.'],
  ], [3200, 7040]),
  H('Why the file matters beyond the warranty'),
  P('Carriers increasingly look for documented roof condition at renewal and rely on maintenance records, or the absence of them, when a claim is reviewed. The same inspection file that keeps a warranty in force is the file that supports insurability and makes capital timing a planning number. Insurance and warranty content here describes market direction and typical manufacturer provisions; it is not a promise about any specific policy, premium, claim or coverage outcome.', { size: 19 }),
  H('The one sentence version'),
  P('A warranty is only as strong as the maintenance and documentation behind it.', { size: 21, bold: true, color: NAVY }),
], '/home/claude/outreach/out/Hustad_Roof_Warranty_OnePager_v1.docx');
