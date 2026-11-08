"""Print the pull windows and SOQL for an exec monthly readout.
Usage:  python readout_month.py                 -> previous calendar month (the default)
        python readout_month.py 2026-10
        python readout_month.py 2026-10 --with prior_month,prior_year
Full FIELDS(ALL) detail is pulled for the readout month only; month-over-month and
year-over-year comparisons come from the three aggregate queries, which cover every
month from January of the prior year to today. Pass --with only when a slide needs
record-level detail for a comparison period (a prior-year month can be migration-heavy)."""
import sys, json
from common import parse_month, month_window, et_window, prior_month, prior_year, tag, label

args = [a for a in sys.argv[1:] if not a.startswith('--')]
extra = []
for a in sys.argv[1:]:
    if a.startswith('--with'):
        extra = a.split('=', 1)[1].split(',') if '=' in a else sys.argv[sys.argv.index(a) + 1].split(',')
year, mo = parse_month(args[0] if args else None)
periods = [(year, mo)]
if 'prior_month' in extra: periods.append(prior_month(year, mo))
if 'prior_year' in extra:  periods.append(prior_year(year, mo))

Q, C = {}, {}
for (y, m) in periods:
    s, e = month_window(y, m); zs, ze = et_window(y, m); t = tag(y, m)
    Q[f'lead_{t}']        = f"SELECT FIELDS(ALL) FROM Lead WHERE CreatedDate >= {zs} AND CreatedDate < {ze} ORDER BY Id LIMIT 200"
    Q[f'opp_created_{t}'] = f"SELECT FIELDS(ALL) FROM Opportunity WHERE CreatedDate >= {zs} AND CreatedDate < {ze} ORDER BY Id LIMIT 200"
    Q[f'opp_closed_{t}']  = f"SELECT FIELDS(ALL) FROM Opportunity WHERE New_Close_Date__c >= {s} AND New_Close_Date__c < {e} AND IsClosed = true ORDER BY Id LIMIT 200"
    C[f'lead_{t}']        = f"SELECT COUNT(Id) n FROM Lead WHERE CreatedDate >= {zs} AND CreatedDate < {ze}"
    C[f'opp_created_{t}'] = f"SELECT COUNT(Id) n FROM Opportunity WHERE CreatedDate >= {zs} AND CreatedDate < {ze}"
    C[f'opp_closed_{t}']  = f"SELECT COUNT(Id) n FROM Opportunity WHERE New_Close_Date__c >= {s} AND New_Close_Date__c < {e} AND IsClosed = true"

a0, _ = et_window(year - 1, 1)
AGG = {
 'lead_monthly':        f"SELECT CALENDAR_YEAR(convertTimezone(CreatedDate)) yr, CALENDAR_MONTH(convertTimezone(CreatedDate)) mo, Is_MQL__c mql, Net_MQL__c net, IsConverted conv, COUNT(Id) n, SUM(SQL_Count__c) sqlc FROM Lead WHERE CreatedDate >= {a0} GROUP BY CALENDAR_YEAR(convertTimezone(CreatedDate)), CALENDAR_MONTH(convertTimezone(CreatedDate)), Is_MQL__c, Net_MQL__c, IsConverted ORDER BY CALENDAR_YEAR(convertTimezone(CreatedDate)), CALENDAR_MONTH(convertTimezone(CreatedDate)), Is_MQL__c, Net_MQL__c, IsConverted",
 'opp_created_monthly': f"SELECT CALENDAR_YEAR(convertTimezone(CreatedDate)) yr, CALENDAR_MONTH(convertTimezone(CreatedDate)) mo, StageName st, COUNT(Id) n, SUM(Amount) amt FROM Opportunity WHERE CreatedDate >= {a0} GROUP BY CALENDAR_YEAR(convertTimezone(CreatedDate)), CALENDAR_MONTH(convertTimezone(CreatedDate)), StageName ORDER BY CALENDAR_YEAR(convertTimezone(CreatedDate)), CALENDAR_MONTH(convertTimezone(CreatedDate)), StageName",
 'closed_won_monthly':  f"SELECT CALENDAR_YEAR(New_Close_Date__c) yr, CALENDAR_MONTH(New_Close_Date__c) mo, CALENDAR_YEAR(CreatedDate) cyr, COUNT(Id) n, SUM(Amount) amt FROM Opportunity WHERE StageName = 'Closed Won' AND New_Close_Date__c >= {a0} GROUP BY CALENDAR_YEAR(New_Close_Date__c), CALENDAR_MONTH(New_Close_Date__c), CALENDAR_YEAR(CreatedDate) ORDER BY CALENDAR_YEAR(New_Close_Date__c), CALENDAR_MONTH(New_Close_Date__c), CALENDAR_YEAR(CreatedDate)",
}
s, e = month_window(year, mo)
print(json.dumps({'readout_month': f'{year}-{mo:02d} ({label(year, mo)})',
                  'window': [s.isoformat(), e.isoformat()],
                  'comparison_detail_pulled': [f'{y}-{m:02d}' for (y, m) in periods[1:]] or 'none: MoM/YoY come from the aggregates',
                  'workdir': f'/home/claude/readout/{year}-{mo:02d}',
                  'datasets': Q, 'count_checks': C, 'aggregates': AGG,
                  'paging': "After each page run: python ingest.py <dataset> <tool_result_path>. Re-run the query with AND Id > '<lastId>' before ORDER BY until a page has < 200 rows. Save each aggregate result verbatim as pages/agg_<name>.json."}, indent=1))
