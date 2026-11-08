"""Print the pull windows and SOQL for a quarter. Usage: python recap_quarter.py 2026-Q3"""
import sys, json
from common import parse_quarter, window, tags, datasets
year, q = parse_quarter(sys.argv[1])
s, e = window(year, q); ps, pe = window(year-1, q)
cur, prev = tags(year, q)
def dt(d): return d.isoformat() + 'T00:00:00Z'
Q = {
 f'lead_{cur}':        f"SELECT FIELDS(ALL) FROM Lead WHERE CreatedDate >= {dt(s)} AND CreatedDate < {dt(e)} ORDER BY Id LIMIT 200",
 f'lead_{prev}':       f"SELECT FIELDS(ALL) FROM Lead WHERE CreatedDate >= {dt(ps)} AND CreatedDate < {dt(pe)} ORDER BY Id LIMIT 200",
 f'opp_created_{cur}': f"SELECT FIELDS(ALL) FROM Opportunity WHERE CreatedDate >= {dt(s)} AND CreatedDate < {dt(e)} ORDER BY Id LIMIT 200",
 f'opp_closed_{cur}':  f"SELECT FIELDS(ALL) FROM Opportunity WHERE New_Close_Date__c >= {s} AND New_Close_Date__c < {e} AND IsClosed = true ORDER BY Id LIMIT 200",
 f'opp_created_{prev}':f"SELECT FIELDS(ALL) FROM Opportunity WHERE CreatedDate >= {dt(ps)} AND CreatedDate < {dt(pe)} ORDER BY Id LIMIT 200",
 f'opp_closed_{prev}': f"SELECT FIELDS(ALL) FROM Opportunity WHERE New_Close_Date__c >= {ps} AND New_Close_Date__c < {pe} AND IsClosed = true ORDER BY Id LIMIT 200",
}
C = {
 f'lead_{cur}':        f"SELECT COUNT(Id) n FROM Lead WHERE CreatedDate >= {dt(s)} AND CreatedDate < {dt(e)}",
 f'lead_{prev}':       f"SELECT COUNT(Id) n FROM Lead WHERE CreatedDate >= {dt(ps)} AND CreatedDate < {dt(pe)}",
 f'opp_created_{cur}': f"SELECT COUNT(Id) n FROM Opportunity WHERE CreatedDate >= {dt(s)} AND CreatedDate < {dt(e)}",
 f'opp_closed_{cur}':  f"SELECT COUNT(Id) n FROM Opportunity WHERE New_Close_Date__c >= {s} AND New_Close_Date__c < {e} AND IsClosed = true",
 f'opp_created_{prev}':f"SELECT COUNT(Id) n FROM Opportunity WHERE CreatedDate >= {dt(ps)} AND CreatedDate < {dt(pe)}",
 f'opp_closed_{prev}': f"SELECT COUNT(Id) n FROM Opportunity WHERE New_Close_Date__c >= {ps} AND New_Close_Date__c < {pe} AND IsClosed = true",
}
a0 = f'{year-1}-01-01'
AGG = {
 'lead_monthly':   f"SELECT CALENDAR_YEAR(CreatedDate) yr, CALENDAR_MONTH(CreatedDate) mo, Is_MQL__c mql, IsConverted conv, COUNT(Id) n, SUM(SQL_Count__c) sqlc FROM Lead WHERE CreatedDate >= {a0}T00:00:00Z GROUP BY CALENDAR_YEAR(CreatedDate), CALENDAR_MONTH(CreatedDate), Is_MQL__c, IsConverted ORDER BY CALENDAR_YEAR(CreatedDate), CALENDAR_MONTH(CreatedDate), Is_MQL__c, IsConverted",
 'opp_created_monthly': f"SELECT CALENDAR_YEAR(CreatedDate) yr, CALENDAR_MONTH(CreatedDate) mo, StageName st, COUNT(Id) n, SUM(Amount) amt FROM Opportunity WHERE CreatedDate >= {a0}T00:00:00Z GROUP BY CALENDAR_YEAR(CreatedDate), CALENDAR_MONTH(CreatedDate), StageName ORDER BY CALENDAR_YEAR(CreatedDate), CALENDAR_MONTH(CreatedDate), StageName",
 'closed_won_monthly': f"SELECT CALENDAR_YEAR(New_Close_Date__c) yr, CALENDAR_MONTH(New_Close_Date__c) mo, CALENDAR_YEAR(CreatedDate) cyr, COUNT(Id) n, SUM(Amount) amt FROM Opportunity WHERE StageName = 'Closed Won' AND New_Close_Date__c >= {a0} GROUP BY CALENDAR_YEAR(New_Close_Date__c), CALENDAR_MONTH(New_Close_Date__c), CALENDAR_YEAR(CreatedDate) ORDER BY CALENDAR_YEAR(New_Close_Date__c), CALENDAR_MONTH(New_Close_Date__c), CALENDAR_YEAR(CreatedDate)",
}
print(json.dumps({'quarter': f'{year}-Q{q}', 'window': [s.isoformat(), e.isoformat()], 'prior_window': [ps.isoformat(), pe.isoformat()],
                  'workdir': f'/home/claude/recap/{year}-Q{q}', 'datasets': Q, 'count_checks': C, 'aggregates': AGG,
                  'paging': "After each page run: python ingest.py <dataset> <tool_result_path>. Re-run the query with AND Id > '<lastId>' before ORDER BY until a page has < 200 rows. Save each aggregate result verbatim as pages/agg_<name>.json."}, indent=1))
