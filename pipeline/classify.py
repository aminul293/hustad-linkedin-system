"""
Hustad LinkedIn Network Activation: classification + scoring engine.
Input: LinkedIn export CSVs. Output: master_contacts.csv with engagement state,
role class, segment, company class, ICP score, tier, and exclusion reasons.
Re-runnable every month on a fresh export (see refresh.py).
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
import pandas as pd, io, re, json, os, sys
from active_accounts import build_active_accounts
ACTIVE_LOOKUP, ACTIVE_SUMMARY = build_active_accounts()
from datetime import datetime

DATA = paths.s(paths.RAW)
OUT = paths.s(paths.WORK)
ME = 'https://www.linkedin.com/in/eric-caturia-a0521136a'
EXPORT_DATE = pd.Timestamp('2026-08-25')

# ----------------------------------------------------------------------------
# 1. Load
# ----------------------------------------------------------------------------
def load_connections(path):
    with open(path, encoding='utf-8') as f:
        txt = f.read()
    idx = txt.find('First Name,Last Name')
    df = pd.read_csv(io.StringIO(txt[idx:]))
    df.columns = [c.strip() for c in df.columns]
    for c in ['First Name', 'Last Name', 'URL', 'Email Address', 'Company', 'Position']:
        df[c] = df[c].fillna('').astype(str).str.strip()
    df['Connected On'] = pd.to_datetime(df['Connected On'], format='%d %b %Y', errors='coerce')
    df['url_key'] = df['URL'].str.lower().str.strip().str.rstrip('/')
    df = df[df['url_key'] != '']            # drop LinkedIn's blank private rows
    df = df.drop_duplicates('url_key')
    return df

def find_raw_file(pattern):
    for fn in os.listdir(DATA):
        if pattern.lower() in fn.lower():
            return os.path.join(DATA, fn)
    return os.path.join(DATA, pattern)

conn = load_connections(find_raw_file('Connections.csv'))
inv = pd.read_csv(find_raw_file('Invitations.csv'))
inv['Sent At'] = pd.to_datetime(inv['Sent At'], format='%m/%d/%y, %I:%M %p', errors='coerce')
msg = pd.read_csv(find_raw_file('messages.csv'))
msg['DATE'] = pd.to_datetime(msg['DATE'], errors='coerce')
msg['from_me'] = msg['SENDER PROFILE URL'].str.lower().str.strip() == ME
endo = pd.read_csv(find_raw_file('Endorsement_Received_Info.csv'))

# ----------------------------------------------------------------------------
# 2. Engagement state from messages / invitations / endorsements
# ----------------------------------------------------------------------------
def counterpart_urls(g):
    others = set()
    for _, r in g.iterrows():
        if r['from_me']:
            for u in str(r['RECIPIENT PROFILE URLS']).split(';'):
                others.add(u.strip().lower().rstrip('/'))
        else:
            others.add(str(r['SENDER PROFILE URL']).strip().lower().rstrip('/'))
    others.discard(ME)
    others.discard('nan')
    return others

msg_state = {}
for cid, g in msg.groupby('CONVERSATION ID'):
    urls = counterpart_urls(g)
    n_me = int(g.from_me.sum()); n_them = int((~g.from_me).sum())
    last = g['DATE'].max(); first = g['DATE'].min()
    folder = g['FOLDER'].iloc[0]
    for u in urls:
        prev = msg_state.get(u, {'n_me': 0, 'n_them': 0, 'last': pd.NaT, 'first': pd.NaT, 'folder': folder})
        prev['n_me'] += n_me; prev['n_them'] += n_them
        prev['last'] = max([d for d in [prev['last'], last] if pd.notna(d)], default=pd.NaT)
        prev['first'] = min([d for d in [prev['first'], first] if pd.notna(d)], default=pd.NaT)
        msg_state[u] = prev

inc_inv = inv[inv.Direction == 'INCOMING'].copy()
inc_inv['url_key'] = inc_inv['inviterProfileUrl'].str.lower().str.strip().str.rstrip('/')
inc_inv_note = set(inc_inv[inc_inv.Message.notna()]['url_key'])
inc_inv_all = set(inc_inv['url_key'])
out_inv = inv[inv.Direction == 'OUTGOING'].copy()
out_inv['url_key'] = out_inv['inviteeProfileUrl'].str.lower().str.strip().str.rstrip('/')
out_inv_dates = out_inv.groupby('url_key')['Sent At'].min().to_dict()
endo_urls = set('https://' + endo['Endorser Public Url'].str.lower().str.strip().str.replace('https://', '', regex=False))

def engagement(row):
    u = row['url_key']
    s = msg_state.get(u)
    if s:
        if s['n_me'] > 0 and s['n_them'] > 0:
            return 'HOT: two-way conversation', s
        if s['n_them'] > 0:
            return 'WARM: they messaged Eric', s
        return 'WARM: Eric messaged, no reply', s
    if u in endo_urls:
        return 'WARM: endorsed Eric', None
    if u in inc_inv_note:
        return 'WARM: sent invite with note', None
    if u in inc_inv_all:
        return 'COLD: they invited Eric, no messages', None
    return 'COLD: no interaction', None

eng = conn.apply(engagement, axis=1)
conn['engagement_state'] = [e[0] for e in eng]
conn['msgs_from_eric'] = [e[1]['n_me'] if e[1] else 0 for e in eng]
conn['msgs_from_them'] = [e[1]['n_them'] if e[1] else 0 for e in eng]
conn['last_message_date'] = [e[1]['last'].date() if (e[1] and pd.notna(e[1]['last'])) else '' for e in eng]
conn['invite_sent_by_eric_on'] = conn['url_key'].map(lambda u: out_inv_dates.get(u, pd.NaT))
conn['invite_source'] = conn['url_key'].map(lambda u: 'Eric invited' if u in out_inv_dates else ('They invited' if u in inc_inv_all else 'Unknown (pre Feb 2026)'))
conn['days_since_connected'] = (EXPORT_DATE - conn['Connected On']).dt.days

# ----------------------------------------------------------------------------
# 3. Role classification (seniority + function) from Position
# ----------------------------------------------------------------------------
def norm(s):
    return re.sub(r'\s+', ' ', str(s).lower().replace('&', ' and ').replace('/', ' ').replace('-', ' ').replace(',', ' ')).strip()

SENIORITY = [
    ('EVP / SVP', r'\b(evp|svp|executive vice president|senior vice president|sr vice president|sr\. vice president|executive vp|senior vp|sr vp)\b'),
    ('Regional / Area VP', r'\b(regional vice president|area vice president|rvp|avp|regional vp|area vp|divisional vice president|division vice president)\b'),
    ('VP', r'\b(vp|vice president)\b'),
    ('C-suite / Owner / Principal', r'\b(ceo|coo|cfo|cio|chief|president|owner|founder|co founder|principal|partner|managing partner|managing director|managing member|proprietor|chairman)\b'),
    ('Director', r'\b(director|head of)\b'),
    ('Asset Manager', r'\basset manager\b'),
    ('Regional / Portfolio Manager', r'\b(regional|portfolio|area manager|district manager|area director|multi site|multisite|multi property|senior regional|regional supervisor|market manager)\b'),
    ('Site Manager (PM/CM/GM)', r'\b(property manager|community manager|general manager|community director|business manager|resident manager|site manager|estate manager|building manager|apartment manager|manager)\b'),
]
def seniority(pos):
    p = norm(pos)
    if not p:
        return 'Unknown'
    if re.search(r'\b(assistant vice president|asst vice president|chief engineer|executive director)\b', p):
        return 'Director'
    for label, rx in SENIORITY:
        if re.search(rx, p):
            return label
    return 'Site Staff / Individual Contributor'

FUNCTION = [
    ('HR / Training / Admin', r'\b(human resources|talent|recruit|training|learning and development|employee development|people and culture|executive assistant|payroll|hr)\b'),
    ('Leasing / Marketing / Revenue', r'\b(business development|strategic partnerships|leasing|marketing|revenue|sales|account executive|account manager|brand|resident experience|customer experience)\b'),
    ('Facilities / Maintenance / Engineering', r'\b(facilit|maintenance|engineer|service manager|building operations|chief engineer|plant|physical plant|environmental services)\b'),
    ('Construction / CapEx / Projects', r'\b(construction|capex|capital improvement|capital project|capital planning|project|renovation|rehab|development|redevelopment|transitions)\b'),
    ('Asset Management / Investments', r'\b(asset|investment|acquisition|portfolio management|fund|capital markets|underwriting|due diligence)\b'),
    ('Procurement / Vendor Mgmt / Risk', r'\b(procurement|purchasing|vendor|supplier|risk|insurance|compliance|contracts)\b'),
    ('Finance / Accounting / IT', r'\b(finance|accounting|controller|cfo|information technology|technology|systems|data|analyst|software|it)\b'),
    ('Operations / Property Mgmt', r'\b(operations|operating|property management|property manager|community manager|regional manager|regional property|general manager|community director|managing director|president|ceo|coo|owner|principal|partner|founder|director of property|vice president|portfolio|district|area|executive director|regional director|manager)\b'),
]
def function(pos):
    p = norm(pos)
    if not p:
        return 'Unknown'
    for label, rx in FUNCTION:
        if re.search(rx, p):
            return label
    return 'Other'

conn['role_seniority'] = conn['Position'].map(seniority)
conn['role_function'] = conn['Position'].map(function)

# ----------------------------------------------------------------------------
# 4. Company classification: segment + company class + fit
# ----------------------------------------------------------------------------
# Manual dictionary for the most common companies and known accounts.
# class: OPERATOR (owner/operator or 3rd party manager, target), CLIENT (active Hustad account),
# HUSTAD (staff), COMMERCIAL_SERVICES (CRE brokerage/services; commercial PM targets inside),
# VENDOR (sells to operators or to Hustad; not a buyer), NONFIT (unrelated)
COMPANY_MAP = {
 # Active or known Hustad accounts (exclude from cold program; route to account owner)
 'yugo': ('CLIENT','Student housing'), 'core spaces': ('CLIENT','Student housing'),
 'cardinal group companies': ('CLIENT','Student housing'), 'cardinal group real estate services': ('CLIENT','Student housing'),
 'cardinal group management': ('CLIENT','Student housing'), 'cardinal group investments, llc': ('CLIENT','Student housing'),
 'asset living': ('CLIENT','Multifamily'), 'asset living -  smp': ('CLIENT','Multifamily'), 'asset living (formerly fc)': ('CLIENT','Multifamily'),
 'the scion group': ('CLIENT','Student housing'), 'campus life & style': ('CLIENT','Student housing'),
 'charter senior living': ('CLIENT','Senior living'), 'dial retirement communities': ('CLIENT','Senior living'),
 'dial realty corp': ('CLIENT','Senior living'), 'dial land development': ('CLIENT','Senior living'),
 'harrison street asset management': ('CLIENT','Student housing'), 'saban real estate llc': ('CLIENT','Multifamily'),
 'monument square investment group': ('CLIENT','Student housing'), 'burlington capital': ('CLIENT','Military / Multifamily'),
 'burlington capital properties': ('CLIENT','Military / Multifamily'), 'capstone on campus management': ('CLIENT','Student housing'),
 'hustad companies, inc': ('HUSTAD','Hustad'),
 # National / large multifamily operators and managers
 'greystar': ('OPERATOR','Multifamily'), 'rpm living': ('OPERATOR','Multifamily'), 'avenue5 residential': ('OPERATOR','Multifamily'),
 'willow bridge property company': ('OPERATOR','Multifamily'), 'zrs management': ('OPERATOR','Multifamily'),
 'pegasus residential': ('OPERATOR','Multifamily'), 'bozzuto': ('OPERATOR','Multifamily'), 'rangewater residential': ('OPERATOR','Multifamily'),
 'rangewater real estate': ('OPERATOR','Multifamily'), 'hawthorne residential partners': ('OPERATOR','Multifamily'),
 'bell partners inc': ('OPERATOR','Multifamily'), 'kairoi residential': ('OPERATOR','Multifamily'), 'vivmark residential': ('OPERATOR','Multifamily'),
 'gallery residential': ('OPERATOR','Multifamily'), 'ram partners, llc': ('OPERATOR','Multifamily'), 'morgan properties': ('OPERATOR','Multifamily'),
 'bh': ('OPERATOR','Multifamily'), 'bh management services, llc': ('OPERATOR','Multifamily'), 'cortland': ('OPERATOR','Multifamily'),
 'continental properties': ('OPERATOR','Multifamily'), 'coastal ridge real estate': ('OPERATOR','Multifamily'),
 'trinity property consultants': ('OPERATOR','Multifamily'), 'drucker + falk, llc': ('OPERATOR','Multifamily'),
 'the morgan group': ('OPERATOR','Multifamily'), 'sares regis group': ('OPERATOR','Multifamily'), 'mission rock residential, llc': ('OPERATOR','Multifamily'),
 'capital square living': ('OPERATOR','Multifamily'), 'capital square': ('OPERATOR','Multifamily'), 'bridge property management': ('OPERATOR','Multifamily'),
 'dp management, llc': ('OPERATOR','Multifamily'), 'bryten®': ('OPERATOR','Multifamily'), 'bryten real estate partners': ('OPERATOR','Multifamily'),
 'valiant residential': ('OPERATOR','Multifamily'), 'harbor group management company': ('OPERATOR','Multifamily'), 'harbor group international': ('OPERATOR','Multifamily'),
 'mill creek residential trust llc': ('OPERATOR','Multifamily'), 'mill creek residential': ('OPERATOR','Multifamily'),
 'redwood living': ('OPERATOR','Build to rent'), 'camden property trust': ('OPERATOR','Multifamily'),
 'apartment management consultants': ('OPERATOR','Multifamily'), 'apartment management consultants llc': ('OPERATOR','Multifamily'),
 'dominium': ('OPERATOR','Affordable multifamily'), 'venterra realty': ('OPERATOR','Multifamily'), 'portico pm': ('OPERATOR','Multifamily'),
 'caf management': ('OPERATOR','Multifamily'), 'brookfield properties': ('OPERATOR','Multifamily / Commercial'), 'irvine company': ('OPERATOR','Multifamily / Commercial'),
 'friedman real estate': ('OPERATOR','Multifamily / Commercial'), 'hillpointe': ('OPERATOR','Multifamily'), 'berger communities': ('OPERATOR','Multifamily'),
 'winncompanies': ('OPERATOR','Affordable multifamily'), 'gables residential': ('OPERATOR','Multifamily'), 'peak living': ('OPERATOR','Multifamily'),
 'peak living, llc': ('OPERATOR','Multifamily'), 'independence realty trust inc.': ('OPERATOR','Multifamily'),
 'hunt military communities': ('OPERATOR','Military housing'), 'olympus property': ('OPERATOR','Multifamily'), 'onni group of companies': ('OPERATOR','Multifamily / Commercial'),
 'preferred apartment communities': ('OPERATOR','Multifamily'), 'american landmark apartments': ('OPERATOR','Multifamily'), 'thrive communities': ('OPERATOR','Multifamily'),
 'air communities': ('OPERATOR','Multifamily'), 'weidner apartment homes': ('OPERATOR','Multifamily'), 'highmark residential': ('OPERATOR','Multifamily'),
 'continental realty corporation': ('OPERATOR','Multifamily / Commercial'), 'aog living': ('OPERATOR','Multifamily'), 'windsor communities': ('OPERATOR','Multifamily'),
 'fogelman properties': ('OPERATOR','Multifamily'), 'thompson thrift': ('OPERATOR','Multifamily'), 'fairfield residential': ('OPERATOR','Multifamily'),
 'kettler': ('OPERATOR','Multifamily'), 'sentral': ('OPERATOR','Multifamily'), 'resprop management': ('OPERATOR','Multifamily'),
 'kittle property group': ('OPERATOR','Affordable multifamily'), 'madison communities': ('OPERATOR','Multifamily'), 'birchstone residential': ('OPERATOR','Multifamily'),
 'quinn residences': ('OPERATOR','Build to rent'), 'united apartment group': ('OPERATOR','Multifamily'), 'the dinerstein companies': ('OPERATOR','Student housing'),
 'village green': ('OPERATOR','Multifamily'), 'the bainbridge companies': ('OPERATOR','Multifamily'), 'embrey': ('OPERATOR','Multifamily'),
 'buckingham companies': ('OPERATOR','Multifamily'), 'waterton': ('OPERATOR','Multifamily'), 'nolan living': ('OPERATOR','Multifamily'),
 'decron properties corp.': ('OPERATOR','Multifamily'), 'conam management corporation': ('OPERATOR','Multifamily'), 'flaherty & collins properties': ('OPERATOR','Multifamily'),
 'birge & held': ('OPERATOR','Multifamily'), 'west shore': ('OPERATOR','Multifamily'), 'essex property trust': ('OPERATOR','Multifamily'),
 'radco': ('OPERATOR','Multifamily'), 'holland partner group': ('OPERATOR','Multifamily'), 'spm, llc': ('OPERATOR','Multifamily'),
 'cws apartment homes': ('OPERATOR','Multifamily'), 'oakwood management company': ('OPERATOR','Multifamily'), 'bellaire multifamily management': ('OPERATOR','Multifamily'),
 'edward rose & sons': ('OPERATOR','Multifamily'), 'goldenrod companies': ('OPERATOR','Multifamily / Commercial'), 'meritus property group': ('OPERATOR','Multifamily'),
 'northwood ravin': ('OPERATOR','Multifamily'), 's2 residential': ('OPERATOR','Multifamily'), 'timberland partners': ('OPERATOR','Multifamily'),
 'vest residential': ('OPERATOR','Multifamily'), 'marquette management': ('OPERATOR','Multifamily'), 'knightvest residential': ('OPERATOR','Multifamily'),
 'arlington properties, inc.': ('OPERATOR','Multifamily'), 'arlington properties, llc': ('OPERATOR','Multifamily'), 'styl residential': ('OPERATOR','Multifamily'),
 'sunrise communities': ('OPERATOR','Multifamily'), 'prime residential': ('OPERATOR','Multifamily'), 'southern management companies': ('OPERATOR','Multifamily'),
 'atrium management company': ('OPERATOR','Multifamily'), 'fitch irick corporation': ('OPERATOR','Multifamily'), 'rr living': ('OPERATOR','Multifamily'),
 'brookside properties, inc.': ('OPERATOR','Multifamily'), 'atlantic pacific companies': ('OPERATOR','Multifamily'), 'cornerstone companies, inc.': ('OPERATOR','Multifamily'),
 'prg real estate': ('OPERATOR','Multifamily'), 'roers companies': ('OPERATOR','Multifamily'), 'monarch investment and management group': ('OPERATOR','Multifamily'),
 'dtn management': ('OPERATOR','Multifamily'), 'trg management company': ('OPERATOR','Multifamily'), 'elmington': ('OPERATOR','Multifamily'),
 'mark-taylor, inc.': ('OPERATOR','Multifamily'), 'griffis residential': ('OPERATOR','Multifamily'), 'berkshire': ('OPERATOR','Multifamily'),
 'amli residential': ('OPERATOR','Multifamily'), 'seldin company': ('OPERATOR','Multifamily'), 'onewall communities': ('OPERATOR','Multifamily'),
 'wilcox communities': ('OPERATOR','Multifamily'), 'fortis property management': ('OPERATOR','Multifamily'), 'chamberlin + associates | real estate management': ('OPERATOR','Multifamily'),
 'weinstein properties': ('OPERATOR','Multifamily'), 'the nrp group llc': ('OPERATOR','Multifamily'), 'price brothers': ('OPERATOR','Multifamily'),
 'gates hudson': ('OPERATOR','Multifamily'), 'cloudten residential': ('OPERATOR','Multifamily'), 'urs properties': ('OPERATOR','Multifamily'),
 'south oxford management': ('OPERATOR','Multifamily'), 'simpson housing lllp / simpson property group llc': ('OPERATOR','Multifamily'),
 'summit property management': ('OPERATOR','Multifamily'), 'hayman company': ('OPERATOR','Multifamily'), 'bedrock property management': ('OPERATOR','Multifamily'),
 'adara communities': ('OPERATOR','Multifamily'), 'barrett & stokely': ('OPERATOR','Multifamily'), 'hilltop residential': ('OPERATOR','Multifamily'),
 'rose associates': ('OPERATOR','Multifamily'), 'beztak': ('OPERATOR','Multifamily'), 'sparrow partners': ('OPERATOR','Build to rent'),
 'tam residential': ('OPERATOR','Multifamily'), 'equity residential': ('OPERATOR','Multifamily'), 'goldoller real estate investments': ('OPERATOR','Multifamily'),
 'cornerstone residential': ('OPERATOR','Multifamily'), 'placemaker properties': ('OPERATOR','Multifamily'), 'cirrus asset management inc.': ('OPERATOR','Multifamily'),
 'lincoln property company': ('OPERATOR','Commercial'), 'lincoln property company cre': ('OPERATOR','Commercial'),
 'hines': ('OPERATOR','Multifamily / Commercial'), 'stream realty partners': ('COMMERCIAL_SERVICES','Commercial'),
 'cushman & wakefield': ('COMMERCIAL_SERVICES','Commercial'), 'cushman & wakefield | thalhimer': ('COMMERCIAL_SERVICES','Commercial'),
 'cbre': ('COMMERCIAL_SERVICES','Commercial'), 'cbre global workplace solutions (gws)': ('COMMERCIAL_SERVICES','Commercial'),
 'jll': ('COMMERCIAL_SERVICES','Commercial'), 'colliers': ('COMMERCIAL_SERVICES','Commercial'), 'newmark': ('COMMERCIAL_SERVICES','Commercial'),
 'transwestern': ('COMMERCIAL_SERVICES','Commercial'), 'avison young | us': ('COMMERCIAL_SERVICES','Commercial'),
 'lee & associates commercial real estate services': ('COMMERCIAL_SERVICES','Commercial'), 'nai np dodge': ('COMMERCIAL_SERVICES','Commercial'),
 'brixmor property group': ('OPERATOR','Retail'), 'phillips edison & company': ('OPERATOR','Retail'), 'link logistics': ('OPERATOR','Industrial'),
 'scannell properties': ('OPERATOR','Industrial'), 'vestar': ('OPERATOR','Retail'), 'hendricks commercial properties': ('OPERATOR','Commercial'),
 'r&r realty group': ('OPERATOR','Commercial'), 'banyan street capital': ('OPERATOR','Commercial'), 'knight commercial': ('OPERATOR','Commercial'),
 'access commercial, llc': ('OPERATOR','Commercial'),
 # Student housing
 'b.hom student living': ('OPERATOR','Student housing'), 'american campus communities': ('OPERATOR','Student housing'), 'landmark properties, inc.': ('OPERATOR','Student housing'),
 'peakmade real estate': ('OPERATOR','Student housing'), 'university partners': ('OPERATOR','Student housing'), 'gmh communities': ('OPERATOR','Student housing'),
 'maslow\'s campus communities': ('OPERATOR','Student housing'), 'article student living': ('OPERATOR','Student housing'), 'tailwind group, inc.': ('OPERATOR','Student housing'),
 'tailwind group': ('OPERATOR','Student housing'), 'campus realty management': ('OPERATOR','Student housing'), 'up campus student living': ('OPERATOR','Student housing'),
 'student quarters': ('OPERATOR','Student housing'), 'the preiss company': ('OPERATOR','Student housing'), 'l3 campus': ('OPERATOR','Student housing'),
 'redstone residential, inc.': ('OPERATOR','Student housing'), 'cls living': ('OPERATOR','Student housing'), 'capstone communities': ('OPERATOR','Student housing'),
 'capstone management partners, llc': ('OPERATOR','Student housing'), 'capstone real estate services, inc.': ('OPERATOR','Multifamily'),
 # Senior living
 'erickson senior living': ('OPERATOR','Senior living'), 'integral senior living': ('OPERATOR','Senior living'), 'solera senior living': ('OPERATOR','Senior living'),
 'welltower™ inc. (nyse:well)': ('OPERATOR','Senior living'),
 # HOA / association management
 'firstservice residential': ('OPERATOR','HOA / Condo'), 'firstservice residential florida': ('OPERATOR','HOA / Condo'), 'castle group': ('OPERATOR','HOA / Condo'),
 'keystone pacific property management': ('OPERATOR','HOA / Condo'), 'kw property management and consulting': ('OPERATOR','HOA / Condo'),
 'realmanage': ('OPERATOR','HOA / Condo'), 'ccmc': ('OPERATOR','HOA / Condo'), 'the management trust': ('OPERATOR','HOA / Condo'),
 'seabreeze management company, inc.': ('OPERATOR','HOA / Condo'), 'cedar management group': ('OPERATOR','HOA / Condo'),
 'common interest management services': ('OPERATOR','HOA / Condo'), 'cardinal management group a realmanage company': ('OPERATOR','HOA / Condo'),
 # SFR / MH / military / other residential
 'progress residential®': ('OPERATOR','Single family rental'), 'invitation homes': ('OPERATOR','Single family rental'), 'tricon residential': ('OPERATOR','Single family rental'),
 'evernest': ('OPERATOR','Single family rental'), 'equity lifestyle properties, inc.': ('OPERATOR','Manufactured housing'), 'sun communities & sun outdoors': ('OPERATOR','Manufactured housing'),
 'yes! communities': ('OPERATOR','Manufactured housing'), 'liberty military housing': ('OPERATOR','Military housing'), 'balfour beatty communities': ('OPERATOR','Military housing'),
 'roots management group': ('OPERATOR','Manufactured housing'),
 # Vendors / non-fit
 'realpage, inc.': ('VENDOR','Software'), 'valet living': ('VENDOR','Amenity services'), 'sodexo': ('VENDOR','Facilities services'),
 'mcdonald\'s': ('NONFIT','Other'), 'd.r. horton': ('NONFIT','Homebuilder'), 'self-employed': ('NONFIT','Other'), 'partners': ('NONFIT','Other'),
 'arqline': ('VENDOR','Other'), 'alexandria real estate equities, inc.': ('OPERATOR','Commercial'),
 'the maintenance academy': ('VENDOR','Training'), 'breakthrough properties': ('OPERATOR','Commercial'), 'fisher brothers': ('OPERATOR','Multifamily / Commercial'),
 'cushman & wakefield': ('OPERATOR','Multifamily / Commercial'), 'cushman & wakefield | thalhimer': ('COMMERCIAL_SERVICES','Commercial'),
 'jll': ('COMMERCIAL_SERVICES','Commercial'), 'cbre': ('COMMERCIAL_SERVICES','Commercial'), 'rockbridge': ('OPERATOR','Hospitality'), 'innvest hotels': ('OPERATOR','Hospitality'), 'nonprofit': ('NONFIT','Other'), 'quishub': ('VENDOR','Automation'), '2 more profits': ('VENDOR','Lead generation'),
}

SEG_KEYWORDS = [
 ('Student housing', r'\b(student|campus|university|college|scholar)\b'),
 ('Senior living', r'\b(senior living|senior care|assisted living|memory care|retirement|life plan|ccrc|senior housing|senior)\b'),
 ('HOA / Condo', r'\b(association|hoa|condominium|condo|community management)\b'),
 ('Retail', r'\b(retail|shopping|centers?|plaza)\b'),
 ('Industrial', r'\b(industrial|logistics|warehouse)\b'),
 ('Hospitality', r'\b(hotels?|hospitality|resorts?|inn|lodging)\b'),
 ('Healthcare', r'\b(health|medical|hospital|clinic)\b'),
 ('Commercial', r'\b(commercial|office|cre)\b'),
 ('Affordable multifamily', r'\b(affordable|housing authority|housing partnership|tax credit|lihtc)\b'),
 ('Single family rental', r'\b(single family|sfr|homes)\b'),
 ('Manufactured housing', r'\b(manufactured|mobile home|rv)\b'),
 ('Military housing', r'\b(military)\b'),
 ('Build to rent', r'\b(build to rent|btr)\b'),
 ('Multifamily', r'\b(residential|apartment|apartments|multifamily|multi family|communities|community|living|properties|property|realty|real estate|capital|partners|group|management|homes|housing|reit|trust|investments|equities|holdings|development|ventures|companies)\b'),
]
VENDOR_KEYWORDS = r'\b(academy|training|institute|coaching|roofing|roof|restoration|construction|contractor|contracting|exteriors|siding|gutter|painting|plumbing|hvac|electric|flooring|landscap|pest|cleaning|janitorial|security|elevator|insurance|adjust|claims|law|legal|attorney|bank|lending|mortgage|credit|title|escrow|software|technology|tech|solutions|consulting|consultants|staffing|recruit|talent|marketing|media|agency|design|architect|engineering|supply|materials|manufactur|gaf|carlisle|firestone|owens corning|sherwin|lowe|home depot|university of|school|church|city of|county|state of|army|navy|air force)\b'

def company_class(company, position):
    c = norm(company)
    p = norm(position)
    if not c:
        return ('UNKNOWN', 'Unknown', 'blank company')
    if c in COMPANY_MAP:
        cls, seg = COMPANY_MAP[c]
        return (cls, seg, 'dictionary')
    # position based segment hints override generic name matching
    if re.search(VENDOR_KEYWORDS, c) and not re.search(r'\b(residential|apartment|multifamily|communities|living|properties|property management|realty|senior living)\b', c):
        return ('VENDOR', 'Vendor / Other', 'vendor keyword')
    seg = None
    for label, rx in SEG_KEYWORDS:
        if re.search(rx, c):
            seg = label; break
    if seg is None:
        # try position keywords
        if re.search(r'\b(student|campus)\b', p): seg = 'Student housing'
        elif re.search(r'\b(senior living|executive director|assisted living|memory care)\b', p): seg = 'Senior living'
        elif re.search(r'\b(commercial|office|retail|industrial)\b', p): seg = 'Commercial'
        elif re.search(r'\b(property|community|regional|asset|facilit|maintenance|portfolio)\b', p): seg = 'Multifamily'
    if seg:
        return ('OPERATOR', seg, 'keyword')
    return ('UNKNOWN', 'Unknown', 'no match')

COMPANY_MAP = {norm(k): v for k, v in COMPANY_MAP.items()}
cc = conn.apply(lambda r: company_class(r['Company'], r['Position']), axis=1)
conn['company_class'] = [x[0] for x in cc]
conn['segment'] = [x[1] for x in cc]
conn['company_class_basis'] = [x[2] for x in cc]
# Gate G2: active accounts from the 2026 opportunity export override everything else
def active_flag(company):
    rec = ACTIVE_LOOKUP.get(str(company).strip().lower())
    if not rec: return ('', '', '')
    return ('VERIFY' if rec['verify'] else 'ACTIVE', rec['crm_company'], rec['account_managers'])
af = conn['Company'].map(active_flag)
conn['active_account_flag'] = [a[0] for a in af]
conn['active_account_crm'] = [a[1] for a in af]
conn['active_account_owner'] = [a[2] for a in af]
conn.loc[conn['active_account_flag'] == 'ACTIVE', 'company_class'] = 'CLIENT'

# Position-level segment override (e.g., 'Regional Manager - Student Housing' at Greystar)
def seg_override(row):
    p = norm(row['Position']); seg = row['segment']
    if re.search(r'\b(student|campus)\b', p): return 'Student housing'
    if re.search(r'\b(senior living|assisted living|memory care)\b', p) and row['company_class'] != 'CLIENT': return 'Senior living'
    if re.search(r'\bexecutive director\b', p) and (seg == 'Senior living' or re.search(r'\b(senior|living|care|retirement|village)\b', norm(row['Company']))): return 'Senior living'
    if re.search(r'\b(commercial|office|retail|industrial)\b', p) and seg in ('Multifamily','Unknown','Commercial','Multifamily / Commercial'): return 'Commercial'
    if re.search(r'\b(association|hoa|condo)\b', p): return 'HOA / Condo'
    return seg
conn['segment'] = conn.apply(seg_override, axis=1)

# Vendor / seller detection at person level (BD/sales titles at non-operator companies)
def seller_flag(row):
    p = norm(row['Position'])
    if row['company_class'] in ('VENDOR','NONFIT'): return True
    if row['company_class'] == 'UNKNOWN' and re.search(r'\b(sales|business development|account executive|account manager|founder|ceo|owner|consultant|coach|recruiter|advisor|broker)\b', p):
        return True
    return False
conn['seller_or_nonfit'] = conn.apply(seller_flag, axis=1)

# ----------------------------------------------------------------------------
# 5. Scoring (ICP fit 0 to 100)
# ----------------------------------------------------------------------------
SEN_PTS = {'C-suite / Owner / Principal': 40, 'EVP / SVP': 38, 'VP': 35, 'Regional / Area VP': 34, 'Director': 30,
           'Asset Manager': 26, 'Regional / Portfolio Manager': 24, 'Site Manager (PM/CM/GM)': 6, 'Site Staff / Individual Contributor': 0, 'Unknown': 2}
FUN_PTS = {'Facilities / Maintenance / Engineering': 30, 'Construction / CapEx / Projects': 30, 'Asset Management / Investments': 28,
           'Procurement / Vendor Mgmt / Risk': 26, 'Operations / Property Mgmt': 24, 'Other': 8, 'Leasing / Marketing / Revenue': 2,
           'HR / Training / Admin': 0, 'Finance / Accounting / IT': 4, 'Unknown': 2}
SEG_PTS = {'Multifamily': 12, 'Student housing': 12, 'Senior living': 12, 'Multifamily / Commercial': 11, 'Commercial': 10, 'Retail': 10,
           'Industrial': 9, 'Build to rent': 10, 'Affordable multifamily': 10, 'Military housing': 10, 'HOA / Condo': 8,
           'Single family rental': 7, 'Manufactured housing': 6, 'Healthcare': 7, 'Hospitality': 7, 'Unknown': 2, 'Vendor / Other': 0, 'Hustad': 0}
CLASS_PTS = {'OPERATOR': 12, 'COMMERCIAL_SERVICES': 8, 'CLIENT': 0, 'HUSTAD': 0, 'VENDOR': 0, 'NONFIT': 0, 'UNKNOWN': 3}
NATIONAL = set(x.lower() for x in """Greystar|RPM Living|Avenue5 Residential|Willow Bridge Property Company|Cushman & Wakefield|Bozzuto|Bell Partners Inc|Morgan Properties|Cortland|BH|BH Management Services, LLC|Camden Property Trust|Equity Residential|AvalonBay Communities|Essex Property Trust|AIR Communities|Independence Realty Trust Inc.|Mill Creek Residential Trust LLC|Mill Creek Residential|Lincoln Property Company|Lincoln Property Company CRE|Fairfield Residential|Gables Residential|Highmark Residential|Pegasus Residential|ZRS Management|RangeWater Residential|RangeWater Real Estate|Hawthorne Residential Partners|FirstService Residential|FirstService Residential Florida|Kairoi Residential|RAM Partners, LLC|Harbor Group Management Company|Harbor Group International|WinnCompanies|Dominium|Weidner Apartment Homes|Bridge Property Management|Apartment Management Consultants|Apartment Management Consultants LLC|Bryten®|Bryten Real Estate Partners|Venterra Realty|Progress Residential®|Invitation Homes|Tricon Residential|American Campus Communities|Landmark Properties, Inc.|PeakMade Real Estate|University Partners|GMH Communities|B.HOM Student Living|Brookfield Properties|Hines|Irvine Company|Related Group|Waterton|Berkshire|AMLI Residential|Sares Regis Group|Holland Partner Group|Fogelman Properties|CONAM Management Corporation|Continental Properties|Edward Rose & Sons|Village Green|KETTLER|Windsor Communities|Olympus Property|American Landmark Apartments|Thrive Communities|Trinity Property Consultants|Coastal Ridge Real Estate|Mission Rock Residential, LLC|Capital Square Living|Capital Square|DP Management, LLC|Valiant Residential|Gallery Residential|Vivmark Residential|Drucker + Falk, LLC|The Morgan Group|Castle Group|KW PROPERTY MANAGEMENT AND CONSULTING|RealManage|CCMC|Keystone Pacific Property Management|Erickson Senior Living|Welltower™ Inc. (NYSE:WELL)|Sun Communities & Sun Outdoors|Equity LifeStyle Properties, Inc.|Hunt Military Communities|Liberty Military Housing|Balfour Beatty Communities|Brixmor Property Group|Phillips Edison & Company|Link Logistics|CBRE|JLL|Colliers|Newmark|Stream Realty Partners|Transwestern|Cardinal Group Companies|Asset Living|Core Spaces|The Scion Group|Yugo|Morgan Properties|Preferred Apartment Communities|Alexandria Real Estate Equities, Inc.|LivCor, a Blackstone Portfolio Company|Sentral|Quinn Residences|Redwood Living|Thompson Thrift|EMBREY|Kittle Property Group|The NRP Group LLC|Elmington|Knightvest Residential|Griffis Residential|Mark-Taylor, Inc.|Monarch Investment and Management Group|Roers Companies|Timberland Partners|Atlantic Pacific Companies|Southern Management Companies|Simpson Housing LLLP / Simpson Property Group LLC|Rose Associates|Beztak|The Bainbridge Companies|Buckingham Companies|Flaherty & Collins Properties|Decron Properties Corp.|West Shore|RADCO|CWS Apartment Homes|Goldenrod Companies|Seldin Company|Peak Living|Peak Living, LLC|Olympus Property|Madison Communities|Birchstone Residential|United Apartment Group|The Dinerstein Companies|Berger Communities|Hillpointe|Friedman Real Estate|Onni Group of Companies|CAF Management|Portico PM|Sunrise Communities|Prime Residential|Atrium Management Company|Fitch Irick Corporation|RR Living|Brookside Properties, Inc.|Cornerstone Companies, Inc.|PRG Real Estate|DTN Management|TRG Management Company|Arlington Properties, Inc.|STYL Residential|Northwood Ravin|S2 Residential|Vest Residential|Marquette Management|Meritus Property Group""".split('|'))
company_counts = conn['Company'].value_counts().to_dict()
def score(row):
    s = SEN_PTS.get(row['role_seniority'], 0) + FUN_PTS.get(row['role_function'], 0) + SEG_PTS.get(row['segment'], 0) + CLASS_PTS.get(row['company_class'], 0)
    n = company_counts.get(row['Company'], 0)
    if row['Company'].lower() in NATIONAL: s += 8
    elif n >= 5: s += 5
    elif n >= 2: s += 3
    d = row['days_since_connected']
    if pd.notna(d) and d <= 14: s += 4
    elif pd.notna(d) and d <= 45: s += 2
    return int(min(100, s))
conn['icp_score'] = conn.apply(score, axis=1)

# ----------------------------------------------------------------------------
# 6. Program eligibility and tiering
# ----------------------------------------------------------------------------
def eligibility(row):
    if row['company_class'] == 'HUSTAD': return ('EXCLUDE', 'Hustad staff')
    if row['company_class'] == 'CLIENT': return ('EXCLUDE', f"Active account (2026 opportunity list: {row['active_account_crm'] or 'MSA reference'}): route to {row['active_account_owner'] or 'account owner'} (Gate G2)")
    if row['active_account_flag'] == 'VERIFY': return ('HOLD', f"Possible active account match ({row['active_account_crm']}): verify before use")
    if row['engagement_state'].startswith('HOT'): return ('EXCLUDE', 'Hot: existing two-way conversation, personal handling')
    if row['engagement_state'].startswith('WARM'): return ('EXCLUDE', 'Warm: prior message or note exists, not a cold target')
    if row['seller_or_nonfit']: return ('EXCLUDE', 'Vendor, seller, or non-fit company')
    if row['company_class'] == 'UNKNOWN' and row['segment'] == 'Unknown': return ('HOLD', 'Company not classified: verify before use')
    if row['role_seniority'] in ('Site Staff / Individual Contributor', 'Unknown'): return ('HOLD', 'Junior or unclear role: verify before use')
    if row['role_function'] in ('Leasing / Marketing / Revenue', 'HR / Training / Admin', 'Finance / Accounting / IT'): return ('HOLD', 'Function outside exterior decision path')
    if row['company_class'] == 'COMMERCIAL_SERVICES' and not re.search(r'\b(property|asset services|facilit|maintenance|engineer|operations|construction|project|portfolio|general manager)\b', norm(row['Position'])): return ('HOLD', 'CRE services firm: verify role is property operations, not brokerage or advisory')
    return ('ELIGIBLE', 'Cold, fits ICP')
el = conn.apply(eligibility, axis=1)
conn['program_status'] = [x[0] for x in el]
conn['status_reason'] = [x[1] for x in el]

def tier(row):
    if row['program_status'] != 'ELIGIBLE': return ''
    s = row['icp_score']
    if row['role_seniority'] in ('Site Manager (PM/CM/GM)', 'Site Staff / Individual Contributor', 'Unknown'): return 'T4 Site level / later'
    if s >= 88: return 'T1 Priority'
    if s >= 76: return 'T2 High'
    if s >= 60: return 'T3 Standard'
    return 'T4 Site level / later'
conn['target_tier'] = conn.apply(tier, axis=1)

# Outreach lane by role function (drives which copy stack is used)
def lane(row):
    f = row['role_function']; sen = row['role_seniority']
    if sen in ('C-suite / Owner / Principal', 'EVP / SVP') : return 'Ownership / Executive'
    if f == 'Asset Management / Investments': return 'Asset management'
    if f == 'Facilities / Maintenance / Engineering': return 'Facilities / Maintenance'
    if f == 'Construction / CapEx / Projects': return 'CapEx / Construction'
    if f == 'Procurement / Vendor Mgmt / Risk': return 'Procurement / Risk'
    if sen in ('VP', 'Regional / Area VP', 'Director'): return 'VP / Director Operations'
    if sen in ('Regional / Portfolio Manager', 'Asset Manager'): return 'Regional / Portfolio'
    return 'Site level'
conn['outreach_lane'] = conn.apply(lane, axis=1)

conn['full_name'] = (conn['First Name'] + ' ' + conn['Last Name']).str.replace(r'\s+', ' ', regex=True).str.strip()
conn['first_name_clean'] = conn['First Name'].str.replace(r'[^A-Za-z\-\' ]', '', regex=True).str.strip().str.split().str[0].fillna('')

cols = ['full_name','First Name','Last Name','first_name_clean','Company','Position','URL','Email Address','Connected On','days_since_connected',
        'invite_source','invite_sent_by_eric_on','engagement_state','msgs_from_eric','msgs_from_them','last_message_date',
        'role_seniority','role_function','outreach_lane','company_class','segment','company_class_basis','seller_or_nonfit',
        'icp_score','program_status','status_reason','target_tier','active_account_flag','active_account_crm','active_account_owner','url_key']
conn = conn[cols].sort_values(['program_status','icp_score'], ascending=[True, False])
conn.to_csv(f'{OUT}/master_contacts.csv', index=False)

print("Total connections:", len(conn))
print(conn['program_status'].value_counts())
print(conn[conn.program_status=='ELIGIBLE']['target_tier'].value_counts())
print(conn[conn.program_status=='ELIGIBLE']['outreach_lane'].value_counts())
print(conn[conn.program_status=='ELIGIBLE']['segment'].value_counts())
print(conn['engagement_state'].value_counts())
