# Slide map: monthly exec deck layout

> Illustrative layout. Every Salesforce figure is stamped "Salesforce live pull <date>" on its slide. Pull ALL slides from ONE pull.

| Slide | Content | Primary source | Filters / notes | Cross-check | DQ flags |
|---|---|---|---|---|---|
| 1-2 | Title, agenda | n/a | n/a | n/a | n/a |
| 3 | Leads by channel MoM and YoY (form fills, MQLs, SQLs, opp $ by channel) | lead_<ym> detail | SQLs = converted MQLs; opp $ = converted-opp Amount by lead channel, **including opps created after month end**; MoM/YoY from the lead_monthly aggregate | channel MQLs sum to total MQLs; SQL $ total = slide 5 | L03, L04, L08 |
| 4 | Paid media spend and closed won MoM/YoY, ROAS, MER, Lost; funnel highlights | opps created and closed won by New Close Date (month, prior month, prior-year month) | Spend is a typed input from the agency worksheet. Closed won attributed per `attribution.md`. Lost = Lost Opportunity **or Closed Lost**. ROAS = attributed CW / paid media; MER = attributed CW / total spend | attributed + excluded = all-in (slide 8) | O03, O14 |
| 5 | Funnel reconciliation: form fills, MQLs, Net MQLs, SQL opps ($), closed won; spend build; CAC | lead_<ym>, closed won by NCD | CAC = total spend / attributed new-logo wins | every card ties to slides 3/4; CAC customer count matches slide 8 | L01, L14 |
| 6 | Closed won by month, prior year vs current | closed_won_monthly + opp_closed_<ym> | Marketing-attributed, New Close Date; do not restate old months | current month = slide 4 | O04, O05, O14 |
| 7, 9 | Dividers | n/a | n/a | n/a | n/a |
| 8 | Lead statuses, opp pipeline stages, CAC | lead_<ym>, opp_created_<ym> | Status labels to API values: Needs Outreach = Not Aware, Outreach Attempted = Working | statuses sum to MQLs; stages sum to opps created | L11, L12, O09 |
| 10 | Paid leads by campaign | lead_<ym> where Lead_Category = PAID | Group by `UTM_Campaign__c`; untagged split by `GCLID__c` presence | PAID totals = slide 3 PAID column | L03, L04 |
| 11 | MQL to SQL conversion by week | lead_<ym> | ET dates, Monday-start weeks, partial weeks labeled | weekly MQLs sum to total MQLs | n/a |

Slides fed by agency or ad-platform data (spend, impressions, retainers): verify only the arithmetic on top of Salesforce figures.
