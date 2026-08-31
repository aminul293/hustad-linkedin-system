# -*- coding: utf-8 -*-
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
import pandas as pd, json, re
from datetime import date, timedelta
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.table import Table, TableStyleInfo
from reply_engine import REPLY_CATEGORIES, DECISION_STYLES, BUYER_STATES, QUALIFICATION, HANDOFF, MEETING_SET, REFERRAL_ASKS, OBJECTIONS
from active_accounts import build_active_accounts
ACTIVE_LOOKUP, ACTIVE_SUMMARY = build_active_accounts()

OUT = paths.s(paths.OUT / 'Hustad_LinkedIn_NewBusiness_Baseline_v1_4.xlsx')
FONT = 'Arial'
NAVY = '1F3A5F'; STEEL = 'D9E2EC'; LIGHT = 'F4F7FA'; YELLOW = 'FFF2CC'; GREEN = 'E2F0D9'; COPPER = 'B7791F'

plan = pd.read_csv(paths.s(paths.PLAN))
master = pd.read_csv(paths.s(paths.MASTER))
research = json.load(open(paths.s(paths.research('companies_research.json'))))

wb = Workbook()
hdr_font = Font(name=FONT, bold=True, color='FFFFFF', size=10)
hdr_fill = PatternFill('solid', fgColor=NAVY)
body_font = Font(name=FONT, size=10)
bold = Font(name=FONT, size=10, bold=True)
title_font = Font(name=FONT, size=14, bold=True, color=NAVY)
sub_font = Font(name=FONT, size=10, italic=True, color='555555')
thin = Side(style='thin', color='BFBFBF')
wrap = Alignment(wrap_text=True, vertical='top')

def style_header(ws, row, ncols):
    for c in range(1, ncols + 1):
        cell = ws.cell(row=row, column=c)
        cell.font = hdr_font; cell.fill = hdr_fill; cell.alignment = Alignment(wrap_text=True, vertical='center')
        cell.border = Border(bottom=thin)

def write_table(ws, df, start_row=1, widths=None, wrap_cols=None, table_name=None):
    cols = list(df.columns)
    for j, c in enumerate(cols, 1):
        ws.cell(row=start_row, column=j, value=c)
    style_header(ws, start_row, len(cols))
    for i, row in enumerate(df.itertuples(index=False), start_row + 1):
        for j, v in enumerate(row, 1):
            if isinstance(v, float) and pd.isna(v): v = None
            if isinstance(v, (pd.Timestamp,)): v = v.date()
            cell = ws.cell(row=i, column=j, value=v)
            cell.font = body_font
            if wrap_cols and cols[j - 1] in wrap_cols: cell.alignment = wrap
    if widths:
        for j, c in enumerate(cols, 1):
            ws.column_dimensions[get_column_letter(j)].width = widths.get(c, 14)
    ws.freeze_panes = ws.cell(row=start_row + 1, column=1)
    if table_name and len(df) > 0:
        ref = f"A{start_row}:{get_column_letter(len(cols))}{start_row + len(df)}"
        t = Table(displayName=table_name, ref=ref)
        t.tableStyleInfo = TableStyleInfo(name='TableStyleLight9', showRowStripes=True)
        ws.add_table(t)
    return start_row + len(df)

# ---------------------------------------------------------------------------
# 1. README
# ---------------------------------------------------------------------------
ws = wb.active; ws.title = 'README'
lines = [
 ('Hustad LinkedIn New Business Track: Baseline Workbook v1.4', title_font),
 ('Single source of truth for the cold outreach program. Built from the LinkedIn data export dated August 25, 2026 (4,839 connections after removing 30 blank private rows), plus messages, invitations and endorsements. Refresh monthly using the Refresh SOP tab. v1.1 applied the 2026 opportunity list as the active account conflict list (Gate G2). v1.2 removed ground up development roles (Hustad does not build) and made the past employer play a shared history opener Eric sends himself. v1.3 rebuilt every message on the Sales Brain arc. v1.4 raised the program to 40 first touches a weekday, which is 1,424 primaries across 966 firms working the eligible pool in about seven weeks, and merged the console and the morning verification desk into one page. This workbook is the analysis copy; the Outreach Desk page is the working surface and holds the live log.', sub_font),
 ('', body_font),
 ('HOW TO USE THIS WORKBOOK', bold),
 ('1. Daily Plan: what to send each day at 11:05. Counts pull live from the Send Queue.', body_font),
 ('2. Send Queue: one row per scheduled message with the exact copy to paste. Mark Status = Sent when sent, add the send time, and record the reply category when a reply arrives. This tab drives every metric.', body_font),
 ('3. Targets: the primary targets plus reserves with research, hooks, why now, the first DM and the shared history opener (touch 2 and 3 text lives on the Send Queue). Reserve rows backfill any primary that fails the pre-send profile check.', body_font),
 ('4. Master Contacts: every connection with engagement state, role class, segment, ICP score, tier and program status. The Live Status column re-checks each company against the Client Accounts tab, so pasting your client list updates exclusions automatically.', body_font),
 ('5. Client Accounts: the 2026 opportunity list (1,217 opportunities, Jan 2 to Aug 26, 2026) summarized by company with account managers, value, states and stages, and the LinkedIn company names each one matched. Client Match List is the one name per row list the formulas read; add new names in the yellow rows and every Live Status updates.', body_font),
 ('5a. Past employer check: the export carries no employment history, so the pre-send profile check includes opening the Experience section. If any past employer is on the Client Match List, type it into the Past Employer column on the Send Queue. The row then flags itself and the Shared History Opener column gives you the message to send instead. You send it yourself; nothing gets handed to anyone else at Hustad. Put the client name where [CLIENT] sits.', body_font),
 ('6. Reply Log: log every reply (date, target, category from the Reply Engine, style, state, next step, owner). Metrics read from here.', body_font),
 ('7. Reply Engine, Buyer Brain, Handoff Routing, Objections: the brain behind replies. Copy the response, fill the braces, send by hand.', body_font),
 ('8. Metrics: weekly sends, replies, reply rate, positive replies, meetings, blocked rows and compliance count. Target reply rate is 20 percent or better.', body_font),
 ('9. Companies: 132 researched companies with the recent news and the source URLs behind every hook. Targets carries the hook; this tab carries its evidence.', body_font),
 ('10. Suppression: permanent do not contact list. Any row here is never messaged again by any program.', body_font),
 ('', body_font),
 ('CELLS YOU EDIT', bold),
 ('Yellow cells are inputs: Send Queue Status, Sent At, Reply Category, Past Employer, Notes; Reply Log rows; Client Match List additions; Suppression rows; Handoff Routing owners. Everything else is generated and should be regenerated from the export, not hand edited.', body_font),
 ('', body_font),
 ('RULES THAT NEVER CHANGE', bold),
 ('Every message is sent by a human. No LinkedIn automation of any kind. Opt out means permanent global suppression the same day. No pricing, warranty promises, claim outcomes or deductible advice in a DM. Facts in a DM must trace to the Companies tab or the row. No em dashes anywhere. Ranges written as X to Y.', body_font),
 ('', body_font),
 ('DECISION RECORD DR-3 (proposed, for Eric to confirm)', bold),
 ('The New Business Track runs at a higher daily volume than the warm program ceiling of five. The program starts Thursday August 27, 2026 after a five person test batch on August 26. First touches ramp 10, 20, 25, 25 then taper; follow ups are levelled so no day exceeds 40 total sends. The per person caps from the Spine still apply: at most 2 touches per 7 days and 1 per 48 hours, every reply halts the sequence, and replies always outrank new sends.', body_font),
]
for i, (t, f) in enumerate(lines, 1):
    c = ws.cell(row=i, column=1, value=t); c.font = f; c.alignment = Alignment(wrap_text=True, vertical='top')
ws.column_dimensions['A'].width = 140

# ---------------------------------------------------------------------------
# 2. Send Queue (built from plan)
# ---------------------------------------------------------------------------
q_rows = []
for _, r in plan.iterrows():
    for n, (dcol, mcol, kind) in enumerate([('touch1_date', 'touch1_dm', 'Touch 1: first DM'), ('touch2_date', 'touch2_dm', 'Touch 2: value follow (give)'), ('touch3_date', 'touch3_dm', 'Touch 3: close the loop')], 1):
        d = r[dcol]
        if r['plan_role'] == 'RESERVE' and n > 1: continue
        q_rows.append({
            'Send Date': pd.to_datetime(d).date() if isinstance(d, str) and d else None,
            'Week': int(float(r['week'])) if r['plan_role'] == 'PRIMARY' else 'Reserve',
            'Day Seq': r['day_seq'] if r['plan_role'] == 'PRIMARY' else None,
            'Target ID': r['target_id'], 'Touch': n, 'Touch Type': kind,
            'Name': r['full_name'], 'Company': r['Company'], 'Position': r['Position'],
            'Lane': r['outreach_lane'], 'Segment': r['segment'], 'Tier': r['target_tier'],
            'LinkedIn URL': r['URL'],
            'Why Now': r['why_now'],
            'Message (copy and paste)': r[mcol], 'Words': len(re.findall(r"[A-Za-z0-9$%'’.,]+", str(r[mcol]))),
            'Pre-send Check': 'Open the profile: confirm title and company; read Experience and enter any past employer that is on the Client Match List; if flagged, send the Shared History Opener instead; skip if the role changed or a reply arrived on an earlier touch',
            'Status': 'Planned', 'Sent At': None, 'Reply Received': None, 'Reply Category': None, 'Notes': None,
            'Past Employer (from profile Experience)': None, 'Past Employer Active Account?': None,
            'Shared History Opener (use only if flagged)': r['past_employer_dm'] if n == 1 else None,
        })
queue = pd.DataFrame(q_rows).sort_values(['Send Date', 'Touch', 'Day Seq'], na_position='last').reset_index(drop=True)
ws = wb.create_sheet('Send Queue')
widths = {'Send Date': 12, 'Week': 7, 'Day Seq': 7, 'Target ID': 9, 'Touch': 7, 'Touch Type': 22, 'Name': 24, 'Company': 26, 'Position': 30, 'Lane': 20, 'Segment': 16, 'Tier': 12,
          'LinkedIn URL': 40, 'Why Now': 40, 'Message (copy and paste)': 90, 'Words': 7, 'Pre-send Check': 30, 'Status': 12, 'Sent At': 16, 'Reply Received': 14, 'Reply Category': 14, 'Notes': 30, 'Past Employer (from profile Experience)': 28, 'Past Employer Active Account?': 30, 'Shared History Opener (use only if flagged)': 80}
last = write_table(ws, queue, widths=widths, wrap_cols=['Message (copy and paste)', 'Why Now', 'Pre-send Check', 'Shared History Opener (use only if flagged)'], table_name='SendQueue')
dv = DataValidation(type='list', formula1='"Planned,Sent,Replied,Skipped,Suppressed,Held"', allow_blank=True)
ws.add_data_validation(dv); dv.add(f"R2:R{last}")
dv2 = DataValidation(type='list', formula1='"R1,R1b,R2,R3,R4,R5,R6,R7,R8,R9,R10,R11,R12,R13,R14,R15,R16,R17,R18,R19,R20"', allow_blank=True)
ws.add_data_validation(dv2); dv2.add(f"U2:U{last}")
for row in range(2, last + 1):
    for col in ['R', 'S', 'T', 'U', 'V', 'W']:
        ws[f"{col}{row}"].fill = PatternFill('solid', fgColor=YELLOW)
    ws[f"X{row}"] = f'=IF(W{row}="","",IF(COUNTIF(\'Client Match List\'!$A:$A,W{row})>0,"YES: use the Shared History Opener, put this company where [CLIENT] sits","no match"))'
    ws[f"X{row}"].font = body_font
    ws[f"A{row}"].number_format = 'yyyy-mm-dd'
    ws.row_dimensions[row].height = 96

# ---------------------------------------------------------------------------
# 3. Daily Plan (formulas over Send Queue)
# ---------------------------------------------------------------------------
ws = wb.create_sheet('Daily Plan')
ws['A1'] = 'Daily Plan: 11:05 to 12:05 Central, Monday to Friday'; ws['A1'].font = title_font
ws['A2'] = 'Counts are live COUNTIFS over the Send Queue. Replies always come first; if replies eat the hour, cut new first touches, never follow ups. Labor Day (Sep 7) has no sends.'; ws['A2'].font = sub_font
headers = ['Date', 'Weekday', 'Week', 'Planned Touch 1 (new)', 'Planned Touch 2', 'Planned Touch 3', 'Total planned', 'Sent (logged)', 'Replies (logged)', 'Block plan']
for j, h in enumerate(headers, 1): ws.cell(row=4, column=j, value=h)
style_header(ws, 4, len(headers))
HOLIDAYS = {date(2026, 9, 7)}
d = date(2026, 8, 26); r = 5
block_std = '11:05 sweep replies (7 min) | 11:12 reply handling (up to 10 min) | 11:22 follow ups Touch 2 then Touch 3 | 11:35 new Touch 1 sends, 60 to 90 seconds each with the pre-send profile check | 12:00 log and tee up tomorrow'
block_mon = '11:05 sweep replies | 11:12 conflict refresh against Client Accounts and Suppression | 11:20 confirm the week (backfill from Reserve) | 11:30 send today\'s queue | 12:00 log'
block_fri = '11:05 sweep replies | 11:12 send Friday queue | 11:35 weekly review: fill Metrics, process opt outs, note blocked rows | 11:55 tee up Monday'
while d <= date(2026, 9, 30):
    if d.weekday() < 5:
        wk = 0 if d <= date(2026, 8, 26) else 1 if d <= date(2026, 9, 2) else 2 if d <= date(2026, 9, 9) else 3 if d <= date(2026, 9, 16) else 4 if d <= date(2026, 9, 23) else 5
        ws.cell(row=r, column=1, value=d).number_format = 'yyyy-mm-dd'
        ws.cell(row=r, column=2, value=d.strftime('%A'))
        ws.cell(row=r, column=3, value='Holiday' if d in HOLIDAYS else wk)
        ws.cell(row=r, column=4, value=f"=COUNTIFS('Send Queue'!$A:$A,A{r},'Send Queue'!$E:$E,1)")
        ws.cell(row=r, column=5, value=f"=COUNTIFS('Send Queue'!$A:$A,A{r},'Send Queue'!$E:$E,2)")
        ws.cell(row=r, column=6, value=f"=COUNTIFS('Send Queue'!$A:$A,A{r},'Send Queue'!$E:$E,3)")
        ws.cell(row=r, column=7, value=f"=SUM(D{r}:F{r})")
        ws.cell(row=r, column=8, value=f"=COUNTIFS('Send Queue'!$A:$A,A{r},'Send Queue'!$R:$R,\"Sent\")+COUNTIFS('Send Queue'!$A:$A,A{r},'Send Queue'!$R:$R,\"Replied\")")
        ws.cell(row=r, column=9, value=f"=COUNTIFS('Reply Log'!$A:$A,A{r})")
        ws.cell(row=r, column=10, value='No sends (Labor Day)' if d in HOLIDAYS else (block_mon if d.weekday() == 0 else block_fri if d.weekday() == 4 else block_std))
        for j in range(1, 11):
            ws.cell(row=r, column=j).font = body_font
            ws.cell(row=r, column=j).alignment = wrap
        r += 1
    d += timedelta(days=1)
for j, w in enumerate([12, 11, 8, 12, 12, 12, 12, 12, 12, 90], 1): ws.column_dimensions[get_column_letter(j)].width = w
ws.freeze_panes = 'A5'

# ---------------------------------------------------------------------------
# 4. Targets
# ---------------------------------------------------------------------------
tcols = ['target_id', 'plan_role', 'week', 'touch1_date', 'touch2_date', 'touch3_date', 'full_name', 'first_name_used', 'Company', 'Position', 'URL', 'Connected On', 'days_since_connected',
         'outreach_lane', 'segment', 'target_tier', 'icp_score', 'role_seniority', 'role_function', 'company_class', 'engagement_state',
         'research_confidence', 'company_hq', 'company_type', 'company_scale', 'company_markets', 'exterior_relevance', 'company_hook', 'why_now', 'overlap_note',
         'proof_used', 'give_offered', 'touch1_dm', 'touch1_words', 'touch2_words', 'touch3_words', 'past_employer_dm']
t = plan[tcols].copy()
t.columns = ['Target ID', 'Plan Role', 'Week', 'Touch 1 Date', 'Touch 2 Date', 'Touch 3 Date', 'Name', 'First Name Used', 'Company', 'Position', 'LinkedIn URL', 'Connected On', 'Days Since Connected',
             'Lane', 'Segment', 'Tier', 'ICP Score', 'Seniority', 'Function', 'Company Class', 'Engagement State',
             'Research Confidence', 'HQ', 'Company Type', 'Scale', 'Markets', 'Exterior Relevance', 'Hook Used', 'Why Now', 'Overlap Note',
             'Proof Used', 'Give Offered', 'Touch 1 DM', 'T1 Words', 'T2 Words', 'T3 Words', 'Shared History Opener']
ws = wb.create_sheet('Targets')
w = {c: 18 for c in t.columns}; w.update({'Name': 24, 'Company': 26, 'Position': 30, 'LinkedIn URL': 36, 'Exterior Relevance': 50, 'Recent News': 60, 'Hook Used': 50, 'Why Now': 40, 'Overlap Note': 40, 'Touch 1 DM': 80, 'Shared History Opener': 70, 'Scale': 40, 'Markets': 40})
last_t = write_table(ws, t, widths=w, wrap_cols=['Exterior Relevance', 'Hook Used', 'Why Now', 'Overlap Note', 'Touch 1 DM', 'Shared History Opener', 'Scale', 'Markets'], table_name='Targets')
nt = len(t.columns)
ws.cell(row=1, column=nt + 1, value='Past Employer (from profile Experience)'); ws.cell(row=1, column=nt + 2, value='Past Employer Active Account?')
style_header(ws, 1, nt + 2)
pe = get_column_letter(nt + 1); pf = get_column_letter(nt + 2)
for row in range(2, last_t + 1):
    ws[f"{pe}{row}"].fill = PatternFill('solid', fgColor=YELLOW)
    ws[f"{pf}{row}"] = f'=IF({pe}{row}="","",IF(COUNTIF(\'Client Match List\'!$A:$A,{pe}{row})>0,"YES: use the Shared History Opener","no match"))'
    ws[f"{pf}{row}"].font = body_font
    ws.row_dimensions[row].height = 110
ws.column_dimensions[pe].width = 28; ws.column_dimensions[pf].width = 30

# ---------------------------------------------------------------------------
# 5. Client Accounts (conflict list) and Suppression
# ---------------------------------------------------------------------------
ws = wb.create_sheet('Client Accounts')
ws['A1'] = 'Active accounts from the 2026 opportunity list (opportunities520260826.csv: 1,217 opportunities, Jan 2 to Aug 26, 2026) plus MSA references. Individuals and internal rows removed.'; ws['A1'].font = sub_font
cadf = ACTIVE_SUMMARY.copy()
r_end = write_table(ws, cadf, start_row=3, widths={'CRM Company (2026 opportunity list)': 34, 'LinkedIn company names matched': 44, 'Account Manager(s)': 30, '2026 opportunities': 12, '2026 sale value': 14, 'Properties': 10, 'States': 26, 'Products': 30, 'Stages seen': 40, 'Last activity': 12, 'Match note': 50}, wrap_cols=['LinkedIn company names matched', 'Account Manager(s)', 'States', 'Products', 'Stages seen', 'Match note'], table_name='ClientAccounts')
for row in range(4, r_end + 1):
    ws.cell(row=row, column=5).number_format = '$#,##0'
    ws.row_dimensions[row].height = 40

ws = wb.create_sheet('Client Match List')
ws['A1'] = 'Company name (as it appears in LinkedIn or the CRM)'; ws['B1'] = 'CRM account'; ws['C1'] = 'Account owner'; ws['D1'] = 'Match type'; ws['E1'] = 'Note'
style_header(ws, 1, 5)
rr = 2
seen = set()
for li, rec in sorted(ACTIVE_LOOKUP.items(), key=lambda x: x[1]['crm_company']):
    for name in [rec['linkedin_company'], rec['crm_company']]:
        if name.lower() in seen: continue
        seen.add(name.lower())
        vals = [name, rec['crm_company'], rec['account_managers'], 'VERIFY' if rec['verify'] else 'ACTIVE', rec['note']]
        for j, v in enumerate(vals, 1):
            c = ws.cell(row=rr, column=j, value=v); c.font = body_font
        rr += 1
ws.cell(row=rr, column=1, value='(add new client or active account names below, one per row; formulas read this column)').font = sub_font
for i in range(rr + 1, rr + 80):
    for col in range(1, 6): ws.cell(row=i, column=col).fill = PatternFill('solid', fgColor=YELLOW)
for col, wdt in zip('ABCDE', [48, 34, 30, 12, 60]): ws.column_dimensions[col].width = wdt
ws.freeze_panes = 'A2'

ws = wb.create_sheet('Suppression')
for j, h in enumerate(['LinkedIn URL', 'Name', 'Company', 'Date', 'Reason (R13 not interested, R20, removed connection, other)', 'Logged by'], 1): ws.cell(row=1, column=j, value=h)
style_header(ws, 1, 6)
for i in range(2, 60):
    for col in range(1, 7): ws.cell(row=i, column=col).fill = PatternFill('solid', fgColor=YELLOW)
for col, wdt in zip('ABCDEF', [44, 24, 26, 12, 40, 14]): ws.column_dimensions[col].width = wdt
ws.freeze_panes = 'A2'

# ---------------------------------------------------------------------------
# 6. Master Contacts (all connections) with live client flag
# ---------------------------------------------------------------------------
mcols = ['full_name', 'Company', 'Position', 'URL', 'Connected On', 'days_since_connected', 'invite_source', 'engagement_state', 'msgs_from_eric', 'msgs_from_them', 'last_message_date',
         'role_seniority', 'role_function', 'outreach_lane', 'company_class', 'segment', 'icp_score', 'target_tier', 'program_status', 'status_reason', 'Email Address', 'active_account_crm', 'active_account_owner']
m = master[mcols].copy()
m.columns = ['Name', 'Company', 'Position', 'LinkedIn URL', 'Connected On', 'Days Since Connected', 'Invite Source', 'Engagement State', 'Msgs From Eric', 'Msgs From Them', 'Last Message',
             'Seniority', 'Function', 'Lane', 'Company Class', 'Segment', 'ICP Score', 'Tier', 'Program Status (export)', 'Status Reason', 'Email (if shared)', 'Active Account (CRM)', 'Account Owner']
m['In Plan'] = m['LinkedIn URL'].isin(set(plan['URL'])).map({True: 'Yes', False: ''})
ws = wb.create_sheet('Master Contacts')
w = {c: 16 for c in m.columns}; w.update({'Name': 26, 'Company': 28, 'Position': 34, 'LinkedIn URL': 40, 'Engagement State': 30, 'Status Reason': 44})
last = write_table(ws, m, widths=w, table_name='MasterContacts')
ncol = len(m.columns)
ws.cell(row=1, column=ncol + 1, value='Client Flag (live)'); ws.cell(row=1, column=ncol + 2, value='Live Status')
style_header(ws, 1, ncol + 2)
cl = get_column_letter(ncol + 1); sl = get_column_letter(ncol + 2)
for row in range(2, last + 1):
    ws[f"{cl}{row}"] = f"=IF(COUNTIFS('Client Match List'!$A:$A,B{row},'Client Match List'!$D:$D,\"ACTIVE\")>0,\"CLIENT\",IF(COUNTIFS('Client Match List'!$A:$A,B{row},'Client Match List'!$D:$D,\"VERIFY\")>0,\"VERIFY\",\"\"))"
    ws[f"{sl}{row}"] = f"=IF({cl}{row}=\"CLIENT\",\"EXCLUDE: active account, route to owner\",IF({cl}{row}=\"VERIFY\",\"HOLD: possible active account, verify\",IF(COUNTIF(Suppression!$A:$A,D{row})>0,\"EXCLUDE: suppressed\",S{row})))"
    ws[f"{cl}{row}"].font = body_font; ws[f"{sl}{row}"].font = body_font
ws.column_dimensions[cl].width = 14; ws.column_dimensions[sl].width = 36

# ---------------------------------------------------------------------------
# 7. Companies (research)
# ---------------------------------------------------------------------------
crow = []
for c in research:
    crow.append({'Company': c.get('company'), 'Confidence': c.get('confidence'), 'HQ': c.get('hq'), 'Company Type': c.get('company_type'), 'Scale': c.get('scale'),
                 'Asset Classes': ', '.join(c.get('asset_classes') or []) if isinstance(c.get('asset_classes'), list) else c.get('asset_classes'),
                 'Markets': c.get('markets'), 'Exterior Relevance': c.get('exterior_relevance'), 'Hook Line (research)': c.get('hook_line'),
                 'Recent News': ' | '.join(f"{n.get('date')}: {n.get('item')} ({n.get('url')})" for n in (c.get('recent_news') or [])),
                 'Sources': ' | '.join(c.get('sources') or []), 'Contacts in plan': int((plan['Company'] == c.get('company')).sum())})
cdf = pd.DataFrame(crow).sort_values('Company')
ws = wb.create_sheet('Companies')
w = {'Company': 30, 'Confidence': 11, 'HQ': 22, 'Company Type': 30, 'Scale': 50, 'Asset Classes': 30, 'Markets': 44, 'Exterior Relevance': 60, 'Hook Line (research)': 50, 'Recent News': 80, 'Sources': 60, 'Contacts in plan': 10}
write_table(ws, cdf, widths=w, wrap_cols=['Scale', 'Markets', 'Exterior Relevance', 'Hook Line (research)', 'Recent News', 'Sources', 'Company Type'], table_name='Companies')
for row in range(2, len(cdf) + 2): ws.row_dimensions[row].height = 120

# ---------------------------------------------------------------------------
# 8. Reply Log
# ---------------------------------------------------------------------------
ws = wb.create_sheet('Reply Log')
cols = ['Date', 'Target ID', 'Name', 'Company', 'Touch # replied to', 'Reply Category (R1 to R20)', 'Positive? (Y/N)', 'Decision Style read', 'Buyer State read', 'What they said (short)', 'Response sent (R id)', 'Next Step', 'Next Due Date', 'Hustad Owner', 'Meeting Set? (Y/N)', 'Meeting Date', 'Referral given? (name)', 'Outcome']
for j, h in enumerate(cols, 1): ws.cell(row=1, column=j, value=h)
style_header(ws, 1, len(cols))
example = [date(2026, 8, 27), 'T000', 'Sample Person', 'Sample Communities', 1, 'R2', 'Y', 'Decisive controller', 'Calm evaluator', 'Open to a call, asked who would join', 'R2', 'Send invite, brief Will Moore', date(2026, 9, 4), 'Will Moore', 'Y', date(2026, 9, 9), '', 'Meeting set (example row, delete)']
for j, v in enumerate(example, 1):
    c = ws.cell(row=2, column=j, value=v); c.font = sub_font
    if isinstance(v, date): c.number_format = 'yyyy-mm-dd'
for i in range(2, 400):
    for col in range(1, len(cols) + 1): ws.cell(row=i, column=col).fill = PatternFill('solid', fgColor=YELLOW)
dv = DataValidation(type='list', formula1='"R1,R1b,R2,R3,R4,R5,R6,R7,R8,R9,R10,R11,R12,R13,R14,R15,R16,R17,R18,R19,R20"', allow_blank=True); ws.add_data_validation(dv); dv.add('F2:F400')
dv = DataValidation(type='list', formula1='"Y,N"', allow_blank=True); ws.add_data_validation(dv); dv.add('G2:G400'); dv.add('O2:O400')
dv = DataValidation(type='list', formula1='"Analytical verifier,Decisive controller,Risk shield,Consensus builder,Operational protector,Price led comparator,Skeptical scar tissue,Unknown"', allow_blank=True); ws.add_data_validation(dv); dv.add('H2:H400')
dv = DataValidation(type='list', formula1='"Calm evaluator,Compressed and overloaded,Guarded and skeptical,Anxious and loss focused,Consensus builder,Ready to move,Unknown"', allow_blank=True); ws.add_data_validation(dv); dv.add('I2:I400')
for j, wdt in enumerate([12, 10, 22, 24, 10, 14, 10, 20, 20, 40, 12, 30, 12, 18, 10, 12, 20, 30], 1): ws.column_dimensions[get_column_letter(j)].width = wdt
ws.freeze_panes = 'A2'

# ---------------------------------------------------------------------------
# 9. Reply Engine
# ---------------------------------------------------------------------------
ws = wb.create_sheet('Reply Engine')
rows = []
for c in REPLY_CATEGORIES:
    rows.append({'ID': c['id'], 'Reply category': c['category'], 'Detection cues': c['cues'], 'Action': c['action'], 'Response (copy, fill braces)': c['response'],
                 'Second message (if any)': c.get('response_to_referred', ''), 'Next step and logging': c['next'], 'Handoff': c['handoff']})
rdf = pd.DataFrame(rows)
write_table(ws, rdf, widths={'ID': 6, 'Reply category': 28, 'Detection cues': 36, 'Action': 44, 'Response (copy, fill braces)': 80, 'Second message (if any)': 60, 'Next step and logging': 40, 'Handoff': 36}, wrap_cols=list(rdf.columns), table_name='ReplyEngine')
for row in range(2, len(rdf) + 2): ws.row_dimensions[row].height = 150

# ---------------------------------------------------------------------------
# 10. Buyer Brain
# ---------------------------------------------------------------------------
ws = wb.create_sheet('Buyer Brain')
ws['A1'] = 'Decision styles (Sales Brain v8 Section 9): read from the reply, then bend the response'; ws['A1'].font = title_font
sdf = pd.DataFrame([{'Style': s['style'], 'Tells in a reply': s['tells'], 'Response modifier': s['modifier'], 'Example reply in this style': s['example']} for s in DECISION_STYLES])
r_end = write_table(ws, sdf, start_row=3, widths={'Style': 22, 'Tells in a reply': 50, 'Response modifier': 50, 'Example reply in this style': 80}, wrap_cols=list(sdf.columns))
for row in range(4, r_end + 1): ws.row_dimensions[row].height = 110
start = r_end + 3
ws.cell(row=start - 1, column=1, value='Buyer states (Section 7): state changes the ask size and format, never the facts').font = title_font
bdf = pd.DataFrame([{'State': s['state'], 'Cues': s['cues'], 'Adjustment': s['adjust']} for s in BUYER_STATES])
r_end = write_table(ws, bdf, start_row=start, wrap_cols=list(bdf.columns))
for row in range(start + 1, r_end + 1): ws.row_dimensions[row].height = 60
start = r_end + 3
ws.cell(row=start - 1, column=1, value='Qualification: one question per message, in the order the conversation allows').font = title_font
qdf = pd.DataFrame(QUALIFICATION)
qdf.columns = ['Field', 'Question (copy)', 'Why it matters']
r_end = write_table(ws, qdf, start_row=start, wrap_cols=list(qdf.columns))
for row in range(start + 1, r_end + 1): ws.row_dimensions[row].height = 50
ws.freeze_panes = None

# ---------------------------------------------------------------------------
# 11. Handoff Routing + Meeting scripts + Referral asks + Objections
# ---------------------------------------------------------------------------
ws = wb.create_sheet('Handoff Routing')
ws['A1'] = 'Handoff routing (editable): who takes the meeting or the lead'; ws['A1'].font = title_font
hdf = pd.DataFrame(HANDOFF); hdf.columns = ['Trigger', 'Owner', 'Backup']
r_end = write_table(ws, hdf, start_row=3, widths={'Trigger': 60, 'Owner': 60, 'Backup': 40}, wrap_cols=list(hdf.columns))
for row in range(4, r_end + 1):
    ws.row_dimensions[row].height = 45
    for col in range(1, 4): ws.cell(row=row, column=col).fill = PatternFill('solid', fgColor=YELLOW)
start = r_end + 3
ws.cell(row=start - 1, column=1, value='Meeting set scripts').font = title_font
mdf = pd.DataFrame([{'Moment': k.replace('_', ' ').title(), 'Copy': v} for k, v in MEETING_SET.items()])
r_end = write_table(ws, mdf, start_row=start, widths={'Moment': 20, 'Copy': 120}, wrap_cols=['Copy'])
for row in range(start + 1, r_end + 1): ws.row_dimensions[row].height = 80
start = r_end + 3
ws.cell(row=start - 1, column=1, value='Referral asks').font = title_font
rdf2 = pd.DataFrame(REFERRAL_ASKS); rdf2.columns = ['When', 'Copy']
r_end = write_table(ws, rdf2, start_row=start, widths={'When': 40, 'Copy': 120}, wrap_cols=list(rdf2.columns))
for row in range(start + 1, r_end + 1): ws.row_dimensions[row].height = 60

ws = wb.create_sheet('Objections')
odf = pd.DataFrame(OBJECTIONS); odf.columns = ['Question they ask', 'Plain answer (adapt, keep under 60 words)']
write_table(ws, odf, widths={'Question they ask': 40, 'Plain answer (adapt, keep under 60 words)': 120}, wrap_cols=list(odf.columns), table_name='Objections')
for row in range(2, len(odf) + 2): ws.row_dimensions[row].height = 70

# ---------------------------------------------------------------------------
# 12. Give Menu
# ---------------------------------------------------------------------------
ws = wb.create_sheet('Give Menu')
gives = [
 ('Fall roof and exterior checklist', 'Facilities, VP Ops, Regional, Site', 'Delivered with this package (Hustad_Fall_Roof_and_Exterior_Checklist_v1.docx). Convert to PDF and host on the portal or send as attachment after a yes.', 'Ready'),
 ('Post turn roof and exterior checklist (student housing note)', 'Student housing contacts', 'Same document, student housing section.', 'Ready'),
 ('Roof warranty one pager: what it covers and what it expects of the owner', 'Ownership, Asset, Procurement, Risk', 'Delivered with this package (Hustad_Roof_Warranty_OnePager_v1.docx). Content from the Proactive Roof Programs deck slides 7 to 9.', 'Ready'),
 ('Sample findings report (one property, redacted)', 'Facilities, Regional', 'Redact one Property Decision Brief (Yugo format) and remove client identifiers. Requires Eric approval before external use.', 'Eric to produce'),
 ('Two page property summary sample (grade, spend history, budget range)', 'Asset management', 'Redacted Property Decision Brief plus the grade and replacement window table. Requires Eric approval.', 'Eric to produce'),
 ('One page portfolio capital view sample', 'Ownership / Executive', 'Redacted version of the mid year portfolio summary page (grade bands, replacement windows, NTE). Requires Eric approval.', 'Eric to produce'),
 ('Bid leveling example (low bidder became the most expensive offer)', 'CapEx / Construction', 'Scope Certainty deck slide 6 plus the leveling worksheet from the sample package. Cleared for external use per the deck.', 'Ready (extract)'),
 ('Inspection and documentation standards one pager', 'Procurement / Risk', 'Build from Proactive Roof Programs deck slides 3, 10, 11 and the Yugo accountability page (monthly, quarterly, annual reporting; closeout package). One page.', 'Eric to produce'),
 ('National Exterior Partner intro deck', 'Anyone who asks for info', 'Existing deck (1. Intro Pitch deck-Hustad.pptx). Fill the rep contact block before sending.', 'Ready'),
 ('Vendor packet (COI, W9, license list)', 'Procurement, vendor registration replies', 'Admin assembles per request.', 'Ready (admin)'),
]
for j, h in enumerate(['Give', 'Used for lanes', 'Source and status notes', 'Status'], 1): ws.cell(row=1, column=j, value=h)
style_header(ws, 1, 4)
for i, g in enumerate(gives, 2):
    for j, v in enumerate(g, 1):
        c = ws.cell(row=i, column=j, value=v); c.font = body_font; c.alignment = wrap
    ws.row_dimensions[i].height = 48
for col, wdt in zip('ABCD', [46, 30, 90, 16]): ws.column_dimensions[col].width = wdt

# ---------------------------------------------------------------------------
# 13. Metrics (weekly, formulas)
# ---------------------------------------------------------------------------
ws = wb.create_sheet('Metrics')
ws['A1'] = 'Weekly metrics (live from Send Queue and Reply Log)'; ws['A1'].font = title_font
ws['A2'] = 'Target: reply rate 20 percent or better on first touches; positive reply rate 10 percent or better; compliance count zero. Fill Meetings and Blocked rows are formulas; Notes is yours.'; ws['A2'].font = sub_font
heads = ['Week', 'Start', 'End', 'Touch 1 sent', 'All sends', 'Replies logged', 'Reply rate (replies / Touch 1 sent)', 'Positive replies', 'Positive rate', 'Meetings set', 'Referrals received', 'Opt outs (R13 + R20)', 'Compliance count (must be 0)', 'Notes']
for j, h in enumerate(heads, 1): ws.cell(row=4, column=j, value=h)
style_header(ws, 4, len(heads))
weeks = [(1, date(2026, 8, 26), date(2026, 9, 2)), (2, date(2026, 9, 3), date(2026, 9, 9)), (3, date(2026, 9, 10), date(2026, 9, 16)), (4, date(2026, 9, 17), date(2026, 9, 23)), (5, date(2026, 9, 24), date(2026, 9, 30))]
for i, (wk, s, e) in enumerate(weeks, 5):
    ws.cell(row=i, column=1, value=wk); ws.cell(row=i, column=2, value=s).number_format = 'yyyy-mm-dd'; ws.cell(row=i, column=3, value=e).number_format = 'yyyy-mm-dd'
    ws.cell(row=i, column=4, value=f"=COUNTIFS('Send Queue'!$A:$A,\">=\"&B{i},'Send Queue'!$A:$A,\"<=\"&C{i},'Send Queue'!$E:$E,1,'Send Queue'!$R:$R,\"Sent\")+COUNTIFS('Send Queue'!$A:$A,\">=\"&B{i},'Send Queue'!$A:$A,\"<=\"&C{i},'Send Queue'!$E:$E,1,'Send Queue'!$R:$R,\"Replied\")")
    ws.cell(row=i, column=5, value=f"=COUNTIFS('Send Queue'!$A:$A,\">=\"&B{i},'Send Queue'!$A:$A,\"<=\"&C{i},'Send Queue'!$R:$R,\"Sent\")+COUNTIFS('Send Queue'!$A:$A,\">=\"&B{i},'Send Queue'!$A:$A,\"<=\"&C{i},'Send Queue'!$R:$R,\"Replied\")")
    ws.cell(row=i, column=6, value=f"=COUNTIFS('Reply Log'!$A:$A,\">=\"&B{i},'Reply Log'!$A:$A,\"<=\"&C{i})")
    ws.cell(row=i, column=7, value=f"=IF(D{i}=0,0,F{i}/D{i})").number_format = '0.0%'
    ws.cell(row=i, column=8, value=f"=COUNTIFS('Reply Log'!$A:$A,\">=\"&B{i},'Reply Log'!$A:$A,\"<=\"&C{i},'Reply Log'!$G:$G,\"Y\")")
    ws.cell(row=i, column=9, value=f"=IF(D{i}=0,0,H{i}/D{i})").number_format = '0.0%'
    ws.cell(row=i, column=10, value=f"=COUNTIFS('Reply Log'!$A:$A,\">=\"&B{i},'Reply Log'!$A:$A,\"<=\"&C{i},'Reply Log'!$O:$O,\"Y\")")
    ws.cell(row=i, column=11, value=f"=COUNTIFS('Reply Log'!$A:$A,\">=\"&B{i},'Reply Log'!$A:$A,\"<=\"&C{i},'Reply Log'!$Q:$Q,\"?*\")")
    ws.cell(row=i, column=12, value=f"=COUNTIFS('Reply Log'!$A:$A,\">=\"&B{i},'Reply Log'!$A:$A,\"<=\"&C{i},'Reply Log'!$F:$F,\"R13\")+COUNTIFS('Reply Log'!$A:$A,\">=\"&B{i},'Reply Log'!$A:$A,\"<=\"&C{i},'Reply Log'!$F:$F,\"R20\")")
    ws.cell(row=i, column=13, value=0).fill = PatternFill('solid', fgColor=YELLOW)
    ws.cell(row=i, column=14, value='').fill = PatternFill('solid', fgColor=YELLOW)
    for j in range(1, 15): ws.cell(row=i, column=j).font = body_font
ws.cell(row=11, column=1, value='Total').font = bold
for j in range(4, 13):
    col = get_column_letter(j)
    if j in (7, 9):
        ws.cell(row=11, column=j, value=f"=IF(D11=0,0,{'F' if j == 7 else 'H'}11/D11)").number_format = '0.0%'
    else:
        ws.cell(row=11, column=j, value=f"=SUM({col}5:{col}9)")
    ws.cell(row=11, column=j).font = bold
ws['A13'] = 'Planned volume (from Send Queue, all statuses)'; ws['A13'].font = bold
ws['A14'] = 'Primary targets'; ws['B14'] = "=COUNTIFS('Send Queue'!$E:$E,1,'Send Queue'!$R:$R,\"<>\")-COUNTIFS('Send Queue'!$E:$E,1,'Send Queue'!$B:$B,\"Reserve\")"
ws['A15'] = 'Reserve targets (initial copy ready, no date)'; ws['B15'] = "=COUNTIFS('Send Queue'!$E:$E,1,'Send Queue'!$B:$B,\"Reserve\")"
ws['A16'] = 'Scheduled follow ups (Touch 2 and 3)'; ws['B16'] = "=COUNTIF('Send Queue'!$E:$E,2)+COUNTIF('Send Queue'!$E:$E,3)"
ws['A17'] = 'Expected replies at 20 percent on primaries'; ws['B17'] = '=ROUND(B14*0.2,0)'
ws['A18'] = 'Expected meetings at 35 percent of replies'; ws['B18'] = '=ROUND(B17*0.35,0)'
for r_ in range(14, 19): ws.cell(row=r_, column=1).font = body_font; ws.cell(row=r_, column=2).font = body_font
for j, wdt in enumerate([8, 12, 12, 12, 10, 12, 16, 12, 12, 12, 12, 12, 16, 40], 1): ws.column_dimensions[get_column_letter(j)].width = wdt

# ---------------------------------------------------------------------------
# 14. Refresh SOP
# ---------------------------------------------------------------------------
ws = wb.create_sheet('Refresh SOP')
sop = [
 ('Monthly refresh: first business day of the month, about 30 minutes inside the block', title_font),
 ('1. LinkedIn: Settings, Data privacy, Get a copy of your data. Select Connections, Messages, Invitations, Endorsements (the same five files used here). Request early; delivery takes minutes to a day.', body_font),
 ('2. Save the new CSVs in the company folder next to this workbook. Keep this workbook plus the two most recent raw exports; delete older exports.', body_font),
 ('3. Run classify.py (delivered with this package) against the new export. It rebuilds master_contacts.csv with engagement state, role class, segment, score, tier and status using the same rules as this baseline.', body_font),
 ('4. Diff against last month, keyed on LinkedIn URL. Events: New connection (add to Master Contacts, score, tier), Removal (URL missing from the new export: add to Suppression), Role change (same URL, new Position), Move (same URL, new Company). Moves and role changes at fitting accounts are Band A triggers.', body_font),
 ('5. Rebuild the plan: run select_targets.py for the next cycle, excluding anyone already in the Send Queue, anyone in Suppression, anyone with a reply in the last 90 days, and any company on Client Accounts. Regenerate copy with copy_engine.py, then research any new companies before sending.', body_font),
 ('6. Re-verify G3: any target whose title or company changed in the export gets re-classified; any target older than 183 days in the plan without a profile check gets re-verified before send.', body_font),
 ('7. Update Metrics for the prior month and archive the Send Queue and Reply Log as a dated copy before loading the new cycle.', body_font),
 ('', body_font),
 ('Files delivered with this workbook (in the outreach package folder)', bold),
 ('classify.py: classification and scoring engine. select_targets.py: target selection and calendar. hooks.py: verified company hooks. copy_engine.py: message composer and QA linter. reply_engine.py: reply brain content. build_workbook.py: rebuilds this workbook. companies_research.json: company research with sources.', body_font),
]
for i, (t_, f) in enumerate(sop, 1):
    c = ws.cell(row=i, column=1, value=t_); c.font = f; c.alignment = Alignment(wrap_text=True, vertical='top')
ws.column_dimensions['A'].width = 140

# Change log sheet
ws = wb.create_sheet('Change Log')
_a = pd.read_csv(paths.s(paths.WORK / 'plan_change_log.csv')); _a['position'] = ''
_b = pd.read_csv(paths.s(paths.WORK / 'plan_change_log_v2.csv'))
_c = pd.read_csv(paths.s(paths.WORK / 'plan_change_log_v3.csv'))
COLS = ['target_id', 'name', 'company', 'position', 'change', 'reason', 'was']
cl_df = pd.concat([_a[COLS], _b[COLS], _c.reindex(columns=COLS)], ignore_index=True).fillna('')
cl_df.columns = ['Target ID', 'Name', 'Company', 'Position', 'Change', 'Reason', 'Was']
ws['A1'] = 'Plan change log: v1.1 Gate G2, v1.2 development roles removed, v1.3 Sales Brain rewrite, v1.4 scaled to 40 first touches a weekday (1,265 primaries added; nobody already sent or scheduled was moved)'; ws['A1'].font = title_font
write_table(ws, cl_df, start_row=3, widths={'Target ID': 10, 'Name': 26, 'Company': 30, 'Position': 34, 'Change': 28, 'Reason': 80, 'Was': 10}, wrap_cols=['Reason'])

# Order sheets
order = ['README', 'Daily Plan', 'Send Queue', 'Targets', 'Reply Log', 'Reply Engine', 'Buyer Brain', 'Handoff Routing', 'Objections', 'Give Menu', 'Metrics', 'Master Contacts', 'Companies', 'Client Accounts', 'Client Match List', 'Suppression', 'Refresh SOP', 'Change Log']
wb._sheets = [wb[n] for n in order]
wb.save(OUT)
print('saved', OUT, 'queue rows', len(queue), 'targets', len(t), 'master', len(m), 'companies', len(cdf))
