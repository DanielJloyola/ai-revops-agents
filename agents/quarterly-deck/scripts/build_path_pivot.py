"""Path slide (form fills → MQLs → Net MQLs → SQLs): detail + pivot workbook and path_numbers.json.
Usage: python build_path_pivot.py 2026-Q3"""
import sys, json, datetime, collections
from zoneinfo import ZoneInfo
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from common import parse_quarter, workdir, tags, load_pages, pulldate, window
year, q = parse_quarter(sys.argv[1]); WD = workdir(year, q); CUR, _ = tags(year, q); PD = pulldate()
ET = ZoneInfo('America/New_York')
recs = load_pages(WD, f'lead_{CUR}')
STATUS = {'Not Aware': 'Needs Outreach', 'Working': 'Outreach Attempted', 'Engaged': 'Engaged', 'Nurture': 'Nurture', 'Unqualified': 'Unqualified', 'Lost Lead': 'Lost Lead', 'Qualified': 'Qualified (SQL)', 'Closed - Partner Referred': 'Closed - Partner Referred'}
MN = {1: 'JAN', 2: 'FEB', 3: 'MAR', 4: 'APRIL', 5: 'MAY', 6: 'JUNE', 7: 'JULY', 8: 'AUG', 9: 'SEPT', 10: 'OCT', 11: 'NOV', 12: 'DEC'}
qmonths = [3*(q-1)+1, 3*(q-1)+2, 3*(q-1)+3]; months = [MN[m] for m in qmonths]
chans = ['ORGANIC', 'PAID', 'DIRECT', 'AI SEARCH', 'OTHER']
def chan(c): return c if c in chans[:4] else 'OTHER'
rows = []
for r in recs:
    d = datetime.datetime.fromisoformat(r['CreatedDate'].replace('+0000', '+00:00')).astimezone(ET)
    mql = 1 if r['Is_MQL__c'] else 0
    rows.append([r['Id'], r.get('Name'), r.get('Company'), d.replace(tzinfo=None), MN[d.month], r.get('Lead_Category__c'), chan(r.get('Lead_Category__c')),
                 r.get('LeadSource'), STATUS.get(r['Status'], r['Status']), mql, 1 if (mql and r['Net_MQL__c']) else 0, 1 if (mql and r['Status'] == 'Qualified') else 0,
                 int(r.get('SQL_Count__c') or 0), 1 if r['IsConverted'] else 0, r.get('ConvertedOpportunityId'), r.get('Unqualified_Reasons__c'), r.get('Lost_Lead_Reasons__c'),
                 r.get('Estimated_Employee_Size__c'), r.get('State_Zip_or_IP__c'), (r.get('City_Zip_IP__c') or '').title() or None, r.get('I_Am_Interested_IN__c'), r.get('How_can_we_help__c'),
                 r.get('Email_Type__c'), 1 if r.get('Personal_Email_Likely__c') else 0, r.get('OwnerId')])
rows.sort(key=lambda x: x[3])
hdr = ['Lead Id', 'Name', 'Company', 'Created Date (ET)', 'Month', 'Lead Category', 'Channel (slide)', 'Lead Source', 'Lead Status', 'Is MQL', 'Net MQL', 'SQL', 'SQL Count', 'Converted', 'Converted Opp Id', 'Unqualified Reason', 'Lost Lead Reason', 'Number of people who need screening(s)', 'State (Zip or IP)', 'City (Zip & IP)', 'I am interested in', 'How can we help?', 'Email Type', 'Personal Email Likely', 'Owner Id']
F = Font(name='Arial', size=10); B = Font(name='Arial', size=10, bold=True); H = Font(name='Arial', size=10, bold=True, color='FFFFFF'); HF = PatternFill('solid', fgColor='1F2A5C'); TOT = PatternFill('solid', fgColor='F2F2F2')
thin = Side(style='thin', color='BFBFBF'); BX = Border(top=thin, bottom=thin, left=thin, right=thin)
wb = Workbook()
det = wb.create_sheet('Detail'); det.append(hdr)
for c in det[1]: c.font = H; c.fill = HF; c.alignment = Alignment(wrap_text=True, vertical='center')
for r in rows: det.append(r)
N = len(rows) + 1
for row in det.iter_rows(min_row=2):
    for c in row: c.font = F
    row[3].number_format = 'm/d/yyyy h:mm'
for i, w in enumerate([20, 24, 28, 16, 8, 13, 13, 30, 18, 7, 8, 6, 8, 9, 20, 30, 22, 16, 10, 16, 30, 40, 12, 9, 20], 1): det.column_dimensions[get_column_letter(i)].width = w
det.freeze_panes = 'B2'; det.auto_filter.ref = det.dimensions
D = lambda col: f"Detail!${col}$2:${col}${N}"
cM, cCh, cMQL, cNet, cSQL, cSrc, cSt, cSize, cState, cInt, cUnq, cLost = ('E', 'G', 'J', 'K', 'L', 'H', 'I', 'R', 'S', 'U', 'P', 'Q')
pv = wb.active; pv.title = 'Pivot overview'
pv['A1'] = f'Q{q} {year} PATH: TOTAL FORM FILLS → MQLs → NET MQLs → SQLs'; pv['A1'].font = Font(name='Arial', size=13, bold=True, color='1F2A5C')
pv['A2'] = f'All counts are COUNTIFS formulas against the Detail tab (1 row per lead created in the quarter, Eastern time). Static pull {PD}.'; pv['A2'].font = F
r = 4; numbers = {}
def block(key, title, flagcol, note):
    global r
    pv.cell(r, 1, title).font = Font(name='Arial', size=11, bold=True, color='1F2A5C'); pv.cell(r, 2, note).font = Font(name='Arial', size=9, italic=True, color='666666'); r += 1
    for j, h in enumerate(['Channel'] + months + [f'Q{q}']): c = pv.cell(r, 1+j, h); c.font = H; c.fill = HF; c.alignment = Alignment(horizontal='center')
    r += 1; first = r; numbers[key] = {}
    for ch in chans:
        pv.cell(r, 1, ch).font = F; vals = []
        for j, m in enumerate(months):
            f = f'=COUNTIFS({D(cM)},"{m}",{D(cCh)},"{ch}"' + (f',{D(flagcol)},1)' if flagcol else ')')
            pv.cell(r, 2+j, f).font = F
            idx = {'': 9, cMQL: 9, cNet: 10, cSQL: 11}[flagcol]
            vals.append(sum(1 for x in rows if x[4] == m and x[6] == ch and (True if not flagcol else x[idx] == 1)))
        numbers[key][ch] = vals
        pv.cell(r, 5, f'=SUM(B{r}:D{r})').font = B; r += 1
    pv.cell(r, 1, 'Month total').font = B; pv.cell(r, 1).fill = TOT
    for j in range(4): c = pv.cell(r, 2+j, f'=SUM({get_column_letter(2+j)}{first}:{get_column_letter(2+j)}{r-1})'); c.font = B; c.fill = TOT
    for rr in range(first-1, r+1):
        for cc in range(1, 6): pv.cell(rr, cc).border = BX
    numbers[key]['month_total'] = [sum(numbers[key][ch][j] for ch in chans) for j in range(3)]
    tot = r; r += 2; return tot
tFF = block('form_fills', f'Q{q} TOTAL FORM FILLS', '', 'every Lead created in the quarter, any status')
tM = block('mqls', f'Q{q} TOTAL MQLs', cMQL, 'Is MQL? = TRUE')
tN = block('net_mqls', f'* Q{q} NET MQLs', cNet, 'Is MQL? = TRUE and Net MQL = TRUE')
tS = block('sqls', f'Q{q} SQLs', cSQL, 'Is MQL? = TRUE and Lead Status = Qualified (SQL)')
pv.cell(r, 1, 'CONVERSION RATES').font = Font(name='Arial', size=11, bold=True, color='1F2A5C'); r += 1
for j, m in enumerate(months + [f'Q{q}']): c = pv.cell(r, 2+j, m); c.font = H; c.fill = HF; c.alignment = Alignment(horizontal='center')
pv.cell(r, 1).fill = HF; r += 1
for label, num, den in (('Form fill → MQL', tM, tFF), ('MQL → Net MQL', tN, tM), ('MQL → SQL', tS, tM), ('Form fill → SQL', tS, tFF)):
    pv.cell(r, 1, label).font = F
    for j in range(4):
        col = get_column_letter(2+j); c = pv.cell(r, 2+j, f'=IF({col}{den}=0,0,{col}{num}/{col}{den})'); c.font = F; c.number_format = '0.0%'
    r += 1
r += 1
pv.cell(r, 1, f'CHANNEL SHARE OF Q{q}').font = Font(name='Arial', size=11, bold=True, color='1F2A5C'); r += 1
for j, h in enumerate(['Channel', 'Form fills', 'MQLs', 'Net MQLs', 'SQLs']): c = pv.cell(r, 1+j, h); c.font = H; c.fill = HF
r += 1
for i, ch in enumerate(chans):
    pv.cell(r, 1, ch).font = F
    for j, t in enumerate((tFF, tM, tN, tS)):
        c = pv.cell(r, 2+j, f'=IF(E{t}=0,0,E{t-5+i}/E{t})'); c.font = F; c.number_format = '0.0%'
    r += 1
for i, w in enumerate([34, 12, 11, 11, 11], 1): pv.column_dimensions[get_column_letter(i)].width = w
dm = wb.create_sheet('MQL dimensions')
dm['A1'] = f'Q{q} {year} MQLs by the standard lead dimensions (Is MQL? = TRUE), by month'; dm['A1'].font = Font(name='Arial', size=13, bold=True, color='1F2A5C')
dm['A2'] = 'COUNTIFS against Detail. “I am interested in” uses a wildcard match (semicolon-joined field), so that table will not sum to the MQL total.'; dm['A2'].font = F
r = 4
mqls = [x for x in rows if x[9]]
def dim_block(title, col, values, wild=False, extra=None):
    global r
    dm.cell(r, 1, title).font = Font(name='Arial', size=11, bold=True, color='1F2A5C'); r += 1
    for j, h in enumerate(['Value'] + months + [f'Q{q}', '% of MQLs']): c = dm.cell(r, 1+j, h); c.font = H; c.fill = HF
    r += 1; first = r
    for v in values:
        dm.cell(r, 1, v if v else 'Not provided').font = F
        for j, m in enumerate(months):
            crit = '""' if v is None else (f'"*{v}*"' if wild else f'"{v}"')
            f = f'=COUNTIFS({D(cM)},"{m}",{D(cMQL)},1,{D(col)},{crit})'
            if extra: f = f[:-1] + f',{extra})'
            dm.cell(r, 2+j, f).font = F
        dm.cell(r, 5, f'=SUM(B{r}:D{r})').font = B
        c = dm.cell(r, 6, f"=E{r}/'Pivot overview'!$E${tM}"); c.font = F; c.number_format = '0.0%'; r += 1
    dm.cell(r, 1, 'Total').font = B
    for j in range(4): c = dm.cell(r, 2+j, f'=SUM({get_column_letter(2+j)}{first}:{get_column_letter(2+j)}{r-1})'); c.font = B; c.fill = TOT
    for rr in range(first-1, r+1):
        for cc in range(1, 7): dm.cell(rr, cc).border = BX
    r += 2
def vals(idx, order=None):
    c = collections.Counter(x[idx] for x in mqls)
    if order: return [o for o in order if o in c] + [k for k, _ in c.most_common() if k not in order and k is not None] + ([None] if None in c else [])
    return [k for k, _ in c.most_common() if k is not None] + ([None] if None in c else [])
dim_block('Lead Category', 'F', vals(5))
dim_block('Lead Source', cSrc, vals(7))
dim_block('Lead Status', cSt, vals(8, ['Needs Outreach', 'Outreach Attempted', 'Engaged', 'Nurture', 'Unqualified', 'Lost Lead', 'Qualified (SQL)']))
dim_block('Number of people who need screening(s)', cSize, vals(17, ['1-5', '6-10', '11-24', '25-49', '50-99', '100-249', '250+', '1-10', '1-24', '100-499', '500-999', '1000+']))
dim_block('Unqualified Reason (Status = Unqualified)', cUnq, [k for k, _ in collections.Counter(x[15] for x in mqls if x[8] == 'Unqualified').most_common() if k] + [None], extra=f'{D(cSt)},"Unqualified"')
dim_block('Lost Lead Reason (Status = Lost Lead)', cLost, [k for k, _ in collections.Counter(x[16] for x in mqls if x[8] == 'Lost Lead').most_common() if k] + [None], extra=f'{D(cSt)},"Lost Lead"')
dim_block('State (Zip or IP): top 15', cState, [k for k, _ in collections.Counter(x[18] for x in mqls).most_common(15) if k] + [None])
ints = collections.Counter()
for x in mqls:
    for v in (x[20] or '').split(';'):
        if v.strip(): ints[v.strip()] += 1
dim_block('I am interested in (wildcard, multi-select)', cInt, [k for k, _ in ints.most_common()], wild=True)
for i, w in enumerate([40, 10, 10, 10, 10, 11], 1): dm.column_dimensions[get_column_letter(i)].width = w
dm.cell(r, 1, f'“How can we help?” is free text; see Detail column V. Summarize the recurring asks in a sentence on the slide if needed.').font = Font(name='Arial', size=9, italic=True)
wb.move_sheet('Detail', offset=2)
p = f'{WD}/out/slide_path_detail_and_pivot.xlsx'; wb.save(p)
numbers.update({'quarter': f'Q{q}', 'year': year, 'months': months, 'pulldate': PD, 'totals': {k: sum(numbers[k]['month_total']) for k in ('form_fills', 'mqls', 'net_mqls', 'sqls')}})
json.dump(numbers, open(f'{WD}/out/path_numbers.json', 'w'), indent=1)
print('saved', p); print(json.dumps(numbers['totals']))
