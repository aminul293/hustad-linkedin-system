"""
Active accounts (Gate G2 conflict list), built from the CRM opportunity export plus the MSA and
testimonial references. Maps each CRM company name to the LinkedIn company name variants found in
the connections export. Any connection whose current company matches is excluded from the cold
program and routed to the account manager instead. Re-run build_active_accounts() whenever a new
opportunity export lands.

The map itself is not in this file. Hustad's client roster and the residential customer names in
the export are commercial and personal data, so they live in data/work/account_map.json, which git
never sees. data/sample/account_map.sample.json is a synthetic stand-in with the same shape, and
is what loads on a fresh clone.
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
import pandas as pd, re

import json

def load_account_map():
    """The real map if it is on this machine, the synthetic one otherwise."""
    for f in (paths.WORK / 'account_map.json', paths.SAMPLE / 'account_map.sample.json'):
        if f.exists():
            m = json.loads(f.read_text())
            crm = {k: (v['linkedin'], v.get('note', '')) for k, v in m['crm_to_linkedin'].items()}
            return crm, set(m.get('individuals_and_internal', [])), f.name
    return {}, set(), '(none)'

# CRM company -> (list of LinkedIn company strings exactly as they appear in the export, note).
# A note starting with 'verify' marks a probable match a human should confirm; those rows are set
# to HOLD rather than EXCLUDE, so a maybe never silently kills a target or silently mails a client.
CRM_TO_LINKEDIN, INDIVIDUALS_AND_INTERNAL, ACCOUNT_MAP_SOURCE = load_account_map()


def load_opportunities(path=paths.s(paths.RAW / 'opportunities_2026.csv')):
    d = pd.read_csv(path)

    # Column aliases
    if 'Company' not in d.columns:
        for c in d.columns:
            if c.lower() in ('company name', 'account name', 'account', 'organization', 'client'):
                d['Company'] = d[c]
                break
    if 'Company' not in d.columns:
        d['Company'] = ''

    if 'ID' not in d.columns:
        if 'Opportunity ID' in d.columns:
            d['ID'] = d['Opportunity ID']
        elif 'Target ID' in d.columns:
            d['ID'] = d['Target ID']
        else:
            d['ID'] = range(1, len(d) + 1)

    if 'Sale Price' not in d.columns:
        d['Sale Price'] = 0.0

    if 'Property' not in d.columns:
        d['Property'] = ''

    if 'Product' not in d.columns:
        d['Product'] = ''

    if 'Stage' not in d.columns:
        if 'Status' in d.columns:
            d['Stage'] = d['Status']
        else:
            d['Stage'] = ''

    if 'Created Date' not in d.columns:
        if 'Stage Date' in d.columns:
            d['Created Date'] = d['Stage Date']
        elif 'Recent Activity' in d.columns:
            d['Created Date'] = d['Recent Activity']
        elif 'Date Sent' in d.columns:
            d['Created Date'] = d['Date Sent']
        else:
            d['Created Date'] = None

    if 'Property Account Manager' not in d.columns:
        if 'Manager' in d.columns:
            d['Property Account Manager'] = d['Manager']
        else:
            d['Property Account Manager'] = ''

    if 'State' not in d.columns:
        d['State'] = ''

    d['Created Date'] = pd.to_datetime(d['Created Date'], errors='coerce')
    d['Company'] = d['Company'].astype(str).str.replace('&amp;', '&').str.strip()
    return d

def build_active_accounts(path=paths.s(paths.RAW / 'opportunities_2026.csv')):
    """Returns (linkedin_company -> record) and a summary dataframe for the Client Accounts tab."""
    d = load_opportunities(path)
    g = d.groupby('Company').agg(opportunities=('ID', 'count'), sale_value=('Sale Price', 'sum'), properties=('Property', 'nunique'),
                                 states=('State', lambda s: ', '.join(sorted(set(s.dropna().astype(str))))),
                                 account_managers=('Property Account Manager', lambda s: ', '.join(sorted(set(s.dropna().astype(str))))),
                                 products=('Product', lambda s: ', '.join(sorted(set(s.dropna().astype(str))))),
                                 stages=('Stage', lambda s: ', '.join(sorted(set(s.dropna().astype(str))))),
                                 last_activity=('Created Date', 'max')).reset_index()
    g = g[~g['Company'].isin(INDIVIDUALS_AND_INTERNAL)]
    summary_rows, lookup = [], {}
    crm_names = set(g['Company'])
    for crm, (li_names, note) in CRM_TO_LINKEDIN.items():
        key = crm.replace(' (per Eric, Mar 2026)', '')
        rec = g[g['Company'] == crm]
        stats = rec.iloc[0].to_dict() if len(rec) else {}
        for li in li_names:
            lookup[li.lower()] = {'crm_company': key, 'linkedin_company': li, 'verify': note.startswith('verify'), 'note': note,
                                 'account_managers': stats.get('account_managers', ''), 'opportunities': stats.get('opportunities', ''),
                                 'sale_value': stats.get('sale_value', ''), 'states': stats.get('states', ''), 'last_activity': stats.get('last_activity', '')}
    # Summary table: every CRM company (with or without LinkedIn matches)
    li_by_crm = {}
    for li, rec in lookup.items():
        li_by_crm.setdefault(rec['crm_company'], []).append(rec['linkedin_company'])
    for _, r in g.sort_values('sale_value', ascending=False).iterrows():
        summary_rows.append({'CRM Company (2026 opportunity list)': r['Company'], 'LinkedIn company names matched': '; '.join(li_by_crm.get(r['Company'], [])) or '(no connections at this company)',
                             'Account Manager(s)': r['account_managers'], '2026 opportunities': int(r['opportunities']), '2026 sale value': round(float(r['sale_value']), 2),
                             'Properties': int(r['properties']), 'States': r['states'], 'Products': r['products'], 'Stages seen': r['stages'],
                             'Last activity': r['last_activity'].date() if pd.notna(r['last_activity']) else '',
                             'Match note': CRM_TO_LINKEDIN.get(r['Company'], ([], ''))[1]})
    for crm, (li_names, note) in CRM_TO_LINKEDIN.items():
        if crm not in crm_names:
            summary_rows.append({'CRM Company (2026 opportunity list)': crm, 'LinkedIn company names matched': '; '.join(li_names), 'Account Manager(s)': '', '2026 opportunities': '', '2026 sale value': '', 'Properties': '', 'States': '', 'Products': '', 'Stages seen': '', 'Last activity': '', 'Match note': note})
    return lookup, pd.DataFrame(summary_rows)

if __name__ == '__main__':
    lookup, summary = build_active_accounts()
    print('map:', ACCOUNT_MAP_SOURCE)
    print(len(lookup), 'LinkedIn company names mapped;', len(summary), 'CRM companies')
    print(summary.head(40).to_string())
