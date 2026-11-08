"""Build the CSV pack from saved pages. Usage: python build_exports.py 2026-Q3"""
import sys, csv, json, collections
from common import *
year, q = parse_quarter(sys.argv[1]); wd = workdir(year, q); out = f'{wd}/out'; PD = pulldate()
cur, prev = tags(year, q); s, e = window(year, q); ps, pe = window(year-1, q)
summary = {}; tie = {}
for ds in datasets(year, q):
    rows = load_pages(wd, ds)
    if not rows: sys.exit(f'{ds}: no pages found in {wd}/pages')
    cols = []
    for r in rows:
        for k in r:
            if k not in cols: cols.append(k)
    fn = f'{out}/{ds}_ALLFIELDS_{PD}.csv'
    with open(fn, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader()
        for r in rows: w.writerow({k: ('' if v is None else v) for k, v in r.items()})
    summary[ds] = (len(rows), len(cols))
    if ds.startswith('lead'):
        mql = sum(1 for r in rows if r['Is_MQL__c']); net = sum(1 for r in rows if r['Is_MQL__c'] and r['Net_MQL__c'])
        sql = sum(1 for r in rows if r['Is_MQL__c'] and r['Status'] == 'Qualified'); conv = sum(1 for r in rows if r['Is_MQL__c'] and r['IsConverted'])
        tie[ds] = f'{len(rows)} leads → {mql} MQLs → {net} Net MQLs → {sql} SQLs ({conv} converted MQLs)'
    else:
        st = collections.Counter(); amt = collections.Counter()
        for r in rows: st[r['StageName']] += 1; amt[r['StageName']] += (r['Amount'] or 0)
        tie[ds] = '; '.join(f'{k}: {st[k]} / ${amt[k]:,.0f}' for k in sorted(st))
# aggregates
agg = load_agg(wd, 'lead_monthly')
if agg:
    a = collections.defaultdict(lambda: [0, 0, 0, 0])
    for r in agg:
        k = (int(r['yr']), int(r['mo'])); n = int(r['n']); a[k][0] += n
        if r['mql']: a[k][1] += n
        if r['mql'] and r['conv']: a[k][2] += n
        a[k][3] += int(r['sqlc'] or 0)
    with open(f'{out}/lead_monthly_summary_{year-1}_{year}.csv', 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['Year', 'Month', 'Leads created', 'MQLs (Is_MQL__c=true)', 'MQLs converted (IsConverted)', 'SQL Count (SUM SQL_Count__c)'])
        for k in sorted(a): w.writerow([k[0], k[1]] + a[k])
    # cross-check current-quarter lead count against pages
    exp = sum(v[0] for k, v in a.items() if k[0] == year and (k[1]-1)//3+1 == q)
    if exp != summary[f'lead_{cur}'][0]: sys.exit(f'lead_{cur}: pages have {summary[f"lead_{cur}"][0]} rows but aggregate says {exp}: missing or duplicated page')
agg = load_agg(wd, 'opp_created_monthly')
if agg:
    with open(f'{out}/opp_created_monthly_by_stage_{year-1}_{year}.csv', 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['Created Year', 'Created Month', 'Current StageName', 'Count', 'Sum Amount'])
        for r in agg: w.writerow([int(r['yr']), int(r['mo']), r['st'], int(r['n']), r['amt'] if r['amt'] is not None else ''])
agg = load_agg(wd, 'closed_won_monthly')
if agg:
    with open(f'{out}/closed_won_monthly_by_new_close_date_{year-1}_{year}.csv', 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['New Close Year', 'New Close Month', 'Opp Created Year', 'Count', 'Sum Amount'])
        for r in agg: w.writerow([int(r['yr']), int(r['mo']), int(r['cyr']), int(r['n']), r['amt']])
# field dictionary
try:
    sch = json.load(open(f'{wd}/pages/schema.json'))
    with open(f'{out}/field_dictionary_Lead_Opportunity.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f); w.writerow(['Object', 'Label', 'API Name', 'Type', 'Length', 'Picklist values', 'Reference to'])
        for obj in sch['details']:
            for fl in obj['fields']:
                w.writerow([obj['name'], fl.get('label'), fl['name'], fl.get('type'), fl.get('length'),
                            '; '.join(p.get('value', p) if isinstance(p, dict) else str(p) for p in fl.get('picklistValues', [])), ','.join(fl.get('referenceTo', []))])
except FileNotFoundError: print('no schema.json: field dictionary skipped')
# README
L = [f'# {year}-Q{q} Marketing Recap: static Salesforce exports', f'Pulled {PD} via the read-only Salesforce connector (SELECT FIELDS(ALL), paged by Id). Values are frozen as of pull time; formula fields are evaluated as of that date. CreatedDate is UTC.', '',
     '| File | Definition | Rows | Cols |', '|---|---|---|---|']
defs = {f'lead_{cur}': f'Lead, CreatedDate {s} to {e - datetime.timedelta(days=1)}', f'lead_{prev}': f'Lead, CreatedDate {ps} to {pe - datetime.timedelta(days=1)}',
        f'opp_created_{cur}': f'Opportunity, CreatedDate {s} to {e - datetime.timedelta(days=1)}', f'opp_closed_{cur}': f'Opportunity, IsClosed = true, New_Close_Date__c {s} to {e - datetime.timedelta(days=1)} (any created year)',
        f'opp_created_{prev}': f'Opportunity, CreatedDate {ps} to {pe - datetime.timedelta(days=1)}', f'opp_closed_{prev}': f'Opportunity, IsClosed = true, New_Close_Date__c {ps} to {pe - datetime.timedelta(days=1)}'}
for ds, (n, c) in summary.items(): L.append(f'| {ds}_ALLFIELDS_{PD}.csv | {defs[ds]} | {n:,} | {c} |')
L += ['', '## Tie-out at pull time'] + [f'- {ds}: {t}' for ds, t in tie.items()]
L += ['', 'Net MQL is only meaningful from the year the framework was deployed (not backfilled). Prior-year lead volume may include a one-time migration batch; footnote YoY slides.']
open(f'{out}/README_{year}-Q{q}_static_exports.md', 'w').write('\n'.join(L) + '\n')
print(json.dumps({'files': summary, 'tie_out': tie}, indent=1))
