"""Build the live CSV pack + exec comparison table. Usage: python build_exports.py [2026-10]"""
import sys, csv, json, collections, datetime
from common import *

args = [a for a in sys.argv[1:] if not a.startswith('--')]
year, mo = parse_month(args[0] if args else None)
wd = workdir(year, mo); out = f'{wd}/out'; PS = pullstamp()
s, e = month_window(year, mo)
# Org-specific settings (illustrative values). Set these for your org.
MIGRATION = {(2025, 9), (2025, 10)}   # (year, month) with one-time data-migration lead batches: footnote any comparison touching them
NET_MQL_START_YEAR = 2026            # first year the Net MQL flag is reliable (framework not backfilled)

# ---- detail CSVs (readout month always; comparison periods if their pages exist) ----
summary = {}; tie = {}
dss = present_datasets(wd)
for ds in base_datasets(year, mo):
    if ds not in dss: sys.exit(f'{ds}: no pages found in {wd}/pages: the readout month must be fully pulled')
for ds in dss:
    rows = load_pages(wd, ds)
    cols = []
    for r in rows:
        for k in r:
            if k not in cols: cols.append(k)
    fn = f'{out}/{ds}_ALLFIELDS_{PS}.csv'
    with open(fn, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader()
        for r in rows: w.writerow({k: ('' if v is None else v) for k, v in r.items()})
    summary[ds] = (len(rows), len(cols))
    if ds.startswith('lead'):
        mql = sum(1 for r in rows if r['Is_MQL__c']); net = sum(1 for r in rows if r['Is_MQL__c'] and r['Net_MQL__c'])
        sq = sum(1 for r in rows if r['Is_MQL__c'] and r['Status'] == 'Qualified'); conv = sum(1 for r in rows if r['Is_MQL__c'] and r['IsConverted'])
        tie[ds] = f'{len(rows)} leads → {mql} MQLs → {net} Net MQLs → {sq} SQLs ({conv} converted MQLs)'
    else:
        st = collections.Counter(); amt = collections.Counter()
        for r in rows: st[r['StageName']] += 1; amt[r['StageName']] += (r['Amount'] or 0)
        tie[ds] = '; '.join(f'{k}: {st[k]} / ${amt[k]:,.0f}' for k in sorted(st))

# ---- aggregates: monthly summary CSVs + the comparison inputs ----
lead_m = {}   # (yr,mo) -> [leads, mqls, net_mqls, conv_mqls, sql_count]
agg = load_agg(wd, 'lead_monthly')
if agg:
    for r in agg:
        k = (int(r['yr']), int(r['mo'])); lead_m.setdefault(k, [0, 0, 0, 0, 0])
        n = int(r['n']); lead_m[k][0] += n
        if r['mql']:
            lead_m[k][1] += n
            if r.get('net'): lead_m[k][2] += n
            if r['conv']: lead_m[k][3] += n
        lead_m[k][4] += int(r['sqlc'] or 0)
    with open(f'{out}/lead_monthly_summary_{year-1}_{year}.csv', 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['Year', 'Month', 'Leads created', 'MQLs (Is_MQL__c=true)', 'Net MQLs (2026+ only)', 'MQLs converted (IsConverted)', 'SQL Count (SUM SQL_Count__c)'])
        for k in sorted(lead_m): w.writerow([k[0], k[1]] + lead_m[k])
    exp = lead_m.get((year, mo), [0])[0]
    got = summary[f'lead_{tag(year, mo)}'][0]
    if exp != got: sys.exit(f'lead_{tag(year, mo)}: pages have {got} rows but aggregate says {exp}: missing or duplicated page, or data changed mid-pull (re-pull the month)')

opp_m = {}    # (yr,mo) -> [count, amount] across all stages
agg = load_agg(wd, 'opp_created_monthly')
if agg:
    with open(f'{out}/opp_created_monthly_by_stage_{year-1}_{year}.csv', 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['Created Year', 'Created Month', 'Current StageName', 'Count', 'Sum Amount'])
        for r in agg:
            k = (int(r['yr']), int(r['mo'])); opp_m.setdefault(k, [0, 0.0])
            opp_m[k][0] += int(r['n']); opp_m[k][1] += float(r['amt'] or 0)
            w.writerow([int(r['yr']), int(r['mo']), r['st'], int(r['n']), r['amt'] if r['amt'] is not None else ''])
    exp = opp_m.get((year, mo), [0])[0]
    got = summary[f'opp_created_{tag(year, mo)}'][0]
    if exp != got: sys.exit(f'opp_created_{tag(year, mo)}: pages have {got} rows but aggregate says {exp}: missing or duplicated page, or data changed mid-pull (re-pull the month)')

cw_m = {}     # (yr,mo) -> [count, amount] Closed Won by New Close Date
agg = load_agg(wd, 'closed_won_monthly')
if agg:
    with open(f'{out}/closed_won_monthly_by_new_close_date_{year-1}_{year}.csv', 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['New Close Year', 'New Close Month', 'Opp Created Year', 'Count', 'Sum Amount'])
        for r in agg:
            k = (int(r['yr']), int(r['mo'])); cw_m.setdefault(k, [0, 0.0])
            cw_m[k][0] += int(r['n']); cw_m[k][1] += float(r['amt'] or 0)
            w.writerow([int(r['yr']), int(r['mo']), int(r['cyr']), int(r['n']), r['amt']])
    rows = load_pages(wd, f'opp_closed_{tag(year, mo)}')
    got = sum(1 for r in rows if r['StageName'] == 'Closed Won')
    exp = cw_m.get((year, mo), [0])[0]
    if exp != got: sys.exit(f'opp_closed_{tag(year, mo)}: pages have {got} Closed Won rows but aggregate says {exp}: missing or duplicated page, or data changed mid-pull (re-pull the month)')

# ---- exec comparison table: readout month vs prior month vs same month last year ----
pm = prior_month(year, mo); py = prior_year(year, mo)
def pct(cur, base):
    if base in (0, None) or cur is None: return ''
    return f'{(cur - base) / base * 100:+.0f}%'
def money(v): return f'${v:,.0f}' if v is not None else '-'
def num(v): return f'{v:,}' if v is not None else '-'
def g(d, k, i): return d[k][i] if k in d else None
measures = [
    ('Leads created',              num,   lambda k: g(lead_m, k, 0)),
    ('MQLs',                       num,   lambda k: g(lead_m, k, 1)),
    ('Net MQLs',                   num,   lambda k: g(lead_m, k, 2)),
    ('Converted MQLs',             num,   lambda k: g(lead_m, k, 3)),
    ('SQL Count',                  num,   lambda k: g(lead_m, k, 4)),
    ('Opps created',               num,   lambda k: g(opp_m, k, 0)),
    ('Created pipeline $',         money, lambda k: g(opp_m, k, 1)),
    ('Closed Won (New Close Date)',num,   lambda k: g(cw_m, k, 0)),
    ('Closed Won $ (New Close Date)', money, lambda k: g(cw_m, k, 1)),
]
comp_rows = []; notes = set()
for name, fmt, fn in measures:
    c, p, y2 = fn((year, mo)), fn(pm), fn(py)
    if name == 'Net MQLs' and py[0] < NET_MQL_START_YEAR:
        y2 = None; yoy = 'n/a¹'
    else:
        yoy = pct(c, y2)
        if py in MIGRATION and name in ('Leads created', 'MQLs'): yoy += '²'; notes.add(2)
    if name == 'Net MQLs': notes.add(1)
    comp_rows.append((name, fmt(c), fmt(p), pct(c, p), fmt(y2) if y2 is not None else '-', yoy))
with open(f'{out}/exec_comparison_{year}-{mo:02d}_{PS}.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['Measure', label(year, mo), label(*pm), 'MoM', label(*py), 'YoY'])
    for r in comp_rows: w.writerow(r)
    w.writerow([])
    w.writerow([f'¹ Net MQL framework not backfilled before {NET_MQL_START_YEAR}: no earlier Net MQL comparisons.'])
    w.writerow(['² Comparison month lead volume includes a one-time data-migration batch.'])

# ---- README ----
L = [f'# {label(year, mo)} Exec Monthly Readout: LIVE Salesforce pull',
     f'Pulled {PS} (UTC) via the read-only Salesforce connector (SELECT FIELDS(ALL), paged by Id).',
     '**Dynamic pull: these are the numbers as of the pull time above, not a frozen snapshot.** Formula fields (Is MQL?, Net MQL) evaluate live; MQL flags, reasons and New Close Dates get backfilled for days after month end, so a re-pull later will differ. Re-pull before the exec meeting rather than reusing this pack. CreatedDate windows are UTC.',
     '', '| File | Definition | Rows | Cols |', '|---|---|---|---|']
for ds, (n, c) in summary.items():
    dy, dm = ds_period(ds); ws, we = month_window(dy, dm)
    kind = {'lead': f'Lead, CreatedDate {ws} to {we - datetime.timedelta(days=1)}',
            'opp_created': f'Opportunity, CreatedDate {ws} to {we - datetime.timedelta(days=1)}',
            'opp_closed': f'Opportunity, IsClosed = true, New_Close_Date__c {ws} to {we - datetime.timedelta(days=1)} (any created year)'}[ds.rsplit('_', 1)[0]]
    L.append(f'| {ds}_ALLFIELDS_{PS}.csv | {kind} | {n:,} | {c} |')
L += ['', '## Tie-out at pull time'] + [f'- {ds}: {t}' for ds, t in tie.items()]
L += ['', f'## {label(year, mo)} vs {label(*pm)} vs {label(*py)}', '',
      '| Measure | ' + ' | '.join([label(year, mo), label(*pm), 'MoM', label(*py), 'YoY']) + ' |',
      '|---|---|---|---|---|---|']
for r in comp_rows: L.append('| ' + ' | '.join(str(x) for x in r) + ' |')
foot = []
if 1 in notes: foot.append(f'¹ Net MQL framework not backfilled before {NET_MQL_START_YEAR}: no earlier Net MQL comparisons.')
if 2 in notes: foot.append(f'² {label(*py)} lead volume includes a one-time data-migration batch.')
L += [''] + foot
open(f'{out}/README_{year}-{mo:02d}_exec_readout.md', 'w').write('\n'.join(L) + '\n')

# ---- field dictionary (optional) ----
try:
    sch = json.load(open(f'{wd}/pages/schema.json'))
    with open(f'{out}/field_dictionary_Lead_Opportunity.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f); w.writerow(['Object', 'Label', 'API Name', 'Type', 'Length', 'Picklist values', 'Reference to'])
        for obj in sch['details']:
            for fl in obj['fields']:
                w.writerow([obj['name'], fl.get('label'), fl['name'], fl.get('type'), fl.get('length'),
                            '; '.join(p.get('value', p) if isinstance(p, dict) else str(p) for p in fl.get('picklistValues', [])), ','.join(fl.get('referenceTo', []))])
except FileNotFoundError: print('no schema.json: field dictionary skipped (fine unless fields changed)')
print(json.dumps({'pullstamp': PS, 'files': summary, 'tie_out': tie,
                  'comparison': [dict(zip(['measure', label(year, mo), label(*pm), 'MoM', label(*py), 'YoY'], r)) for r in comp_rows]}, indent=1))
