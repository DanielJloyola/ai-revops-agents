# Slide map (Marketing Recap deck layout, slides 11-28)

> Illustrative layout. Edit `SLIDES` in `scripts/build_slide_map.py` if the deck changes; this file is the human-readable copy.

| Slide | Content | Primary file | Supporting |
|---|---|---|---|
| 11 | Section divider: Marketing Results | n/a | n/a |
| 12 | Path: form fills, MQLs, Net MQLs, SQLs by channel by month | lead_<q> | lead_monthly_summary |
| 13 | Unqualified MQLs by reason | lead_<q> | DQ workbook (L01, L12, L07) |
| 14 | Unqualified "Other" sub-reasons parsed from notes | lead_<q> | n/a |
| 15 | Lost MQLs by reason by month | lead_<q> | DQ (L02) |
| 16 | Leads by channel with created opp $ (join on ConvertedOpportunityId) | lead_<q> | opp_created_<q> |
| 17 | Spend, created opp $, Closed Won, ROAS, MER, Lost by month | opp_created_<q> | opp_closed_<q>, closed_won_monthly, opp_created_monthly; spend from agency |
| 18 | Same as 17 without the quarter's outlier deal(s) | opp_closed_<q> | opp_created_<q> |
| 19 | Funnel reconciliation (three pipeline scopes, Net MQL bridge, spend build) | lead_<q> | all opp files + summaries |
| 20 | Section divider: YoY | n/a | n/a |
| 21 | MQLs by channel YoY with MQL-stage pipeline | lead_<q>, lead_<pq> | opp_created_<q>, opp_created_<pq> |
| 22 | Created pipeline by month YoY with SQL counts | opp_created_monthly | opp_created_<q>, opp_created_<pq>, lead_monthly |
| 23 | Closed Won by month YoY (New Close Date) | closed_won_monthly | opp_closed_<q>, opp_closed_<pq> |
| 24 | Section divider: Awareness | n/a | n/a |
| 25 | Awareness campaign (ad platform) | not Salesforce | n/a |
| 26 | Section divider: Sales Stages | n/a | n/a |
| 27 | Lead statuses by month; opp stages by month; CAC | lead_<q> | opp_created_<q>, opp_closed_<q>, summaries; spend from agency |
| 28 | Total created opp $ by channel YoY, all sources | opp_created_<q>, opp_created_<pq> | DQ (O01, O02) |
