"""Slide-to-report map workbook. Usage: python build_slide_map.py 2026-Q3
Edit SLIDES when the deck layout changes (references/slide_map.md is the readable copy)."""
import sys
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from common import parse_quarter, workdir, tags, pulldate
year, q = parse_quarter(sys.argv[1]); WD = workdir(year, q); CUR, PREV = tags(year, q); PD = pulldate(); Q = f'Q{q}'; Y = year; PY = year-1
L = f'lead_{CUR}_ALLFIELDS_{PD}.csv'; LP = f'lead_{PREV}_ALLFIELDS_{PD}.csv'
OC = f'opp_created_{CUR}_ALLFIELDS_{PD}.csv'; OX = f'opp_closed_{CUR}_ALLFIELDS_{PD}.csv'
OCP = f'opp_created_{PREV}_ALLFIELDS_{PD}.csv'; OXP = f'opp_closed_{PREV}_ALLFIELDS_{PD}.csv'
LM = f'lead_monthly_summary_{PY}_{Y}.csv'; OM = f'opp_created_monthly_by_stage_{PY}_{Y}.csv'; CW = f'closed_won_monthly_by_new_close_date_{PY}_{Y}.csv'
DQ = f'data_quality_flags_{PD}.xlsx'
SLIDES = [
 (11, f'{Q} MARKETING RESULTS (section divider)', 'Divider: no data', '', '', '', '', '', '', '', ''),
 (12, f'{Q} PATH: TOTAL FORM FILLS TO MQLS TO SQLS', 'Four monthly charts: total leads, MQLs, Net MQLs, SQLs by channel', 'Lead', L, LM,
  'Leads = every row. MQLs = Is_MQL__c = TRUE. Net MQLs = Is_MQL__c AND Net_MQL__c. SQLs = Is_MQL__c AND Status = Qualified.', 'Month of CreatedDate (Eastern) × Lead_Category__c; REFERRAL + DRIP CAMPAIGN + UNKNOWN → Other.',
  f'Monthly totals must equal {LM} for the quarter.', 'L04, L11, L10', ''),
 (13, f'{Q} UNQUALIFIED LEADS', 'Unqualified MQLs by Unqualified Reason', 'Lead', L, DQ, 'Is_MQL__c = TRUE AND Status = Unqualified', 'Unqualified_Reasons__c (blanks as “No reason recorded”)', 'Total = Unqualified count in the slide-12 status split', 'L01, L12, L07', ''),
 (14, f'{Q} UNQUALIFIED – “OTHER” LEADS DETAILS', 'Sub-reasons for “Other” parsed from rep notes', 'Lead', L, '', 'Is_MQL__c = TRUE AND Status = Unqualified AND Unqualified_Reasons__c = Other', 'Keyword-parse Unqualified_Note__c, Lost_or_Unqualified_Notes__c, How_can_we_help__c, form_comments__c', 'Sub-reason total = “Other” row on slide 13', 'L01', ''),
 (15, f'{Q} LOST LEADS – ACTIONABLE BUT LOST', 'Lost MQLs by Lost Lead Reason by month; speed-to-lead vs competitive callout', 'Lead', L, DQ, 'Is_MQL__c = TRUE AND Status = Lost Lead', 'Lost_Lead_Reasons__c × month (use the picklist values in the export, they change)', 'Total = Lost Lead count in the slide-12 status split', 'L02, L12', ''),
 (16, f'{Q} LEADS BY CHANNEL AND OPP REVENUE', 'Month × channel: form fills, MQLs, SQLs, created opp $; avg deal size', 'Lead + Opportunity', L, OC + ' ; ' + DQ, f'Counts from Lead. Opp $: join Lead.ConvertedOpportunityId → Opportunity.Id in {OC}, sum Amount.', 'Lead_Category__c × month', 'Channel columns sum to slide-12 totals; converted MQLs exceed joined opps (no-opp conversions)', 'L08, O03, O01', ''),
 (17, f'{Q} LEADS BY CHANNEL: SPEND, OPP REVENUE, CLOSED WON', 'Monthly spend, created opp $, Closed Won, ROAS, MER, Lost', 'Opportunity', OC, OX + ' ; ' + CW + ' ; ' + OM, f'Created $: SUM Amount by CreatedDate month from {OC}. Closed Won: StageName = Closed Won by New_Close_Date__c month from {OX}. Lost: Lost Opportunity / Closed Lost by CreatedDate month.', 'Month; ROAS = closed won ÷ paid media; MER = closed won ÷ (SEO + paid + agency %)', f'Closed Won by month = {CW}', 'O06, O07, O05', 'Spend from the agency worksheet'),
 (18, f'{Q} … CLOSED WON WITHOUT [OUTLIER]', 'Slide 17 with the quarter’s outlier deal(s) removed; avg deal size won / won+lost', 'Opportunity', OX, OC + ' ; ' + CW, f'Sort {OX} by Amount; exclude the outlier(s) and any Closed Won whose CreatedDate year ≠ {Y}.', 'Avg won = $ ÷ count; avg won+lost = (won $ + lost $) ÷ (won + lost count)', 'Ex-outlier = slide 17 minus excluded rows', 'O06, O03', 'Spend as slide 17'),
 (19, f'{Q} FUNNEL RECONCILIATION', 'Leads → MQLs → Net MQLs → SQL opps → Closed Won; Net MQL bridge; spend build', 'Lead + Opportunity', L, OC + ' ; ' + OX + ' ; ' + LM + ' ; ' + CW, 'Net MQL bridge: MQLs − unqualified with a removal reason. Three scopes: MQL pipeline (joined), total-leads pipeline (all converted), total opps (every opp created in quarter).', 'See README tie-out', 'Every number ties to slides 12, 13, 15, 16, 17', 'L08, O01, O03', 'Spend build from agency worksheet'),
 (20, f'{Q}, YOY OVERVIEW (section divider)', 'Divider: no data', '', '', '', '', '', '', '', ''),
 (21, f'MQL {Q} View YoY LEADS BY CHANNEL', f'{PY} vs {Y} {Q} MQLs by channel with MQL-stage pipeline', 'Lead + Opportunity', L + ' ; ' + LP, OC + ' ; ' + OCP + ' ; ' + LM, 'MQLs = Is_MQL__c = TRUE per year; pipeline via ConvertedOpportunityId → Amount in the matching year’s opp file.', 'Lead_Category__c × year; footnote Unknown-category delta', f'MQL totals from {LM}. Never show Net MQL for {PY}.', 'L04, L03, L11, L05', ''),
 (22, f'SQL Quarterly View YoY – Pipeline Generated', f'Monthly {PY} vs {Y} created opp $ with SQL counts; anomaly callouts', 'Opportunity', OM, OC + ' ; ' + OCP + ' ; ' + LM, f'SUM Amount by CreatedDate month (all stages, all sources) from {OM}; SQL counts = converted MQLs by month from {LM}.', 'Month × year', 'Monthly sums = detail-file sums', 'O03, O01', 'Decide the outlier rule; list top 3 deals per year'),
 (23, f'SQL Quarterly View MoM {Q} – Closed Won', f'Monthly {PY} vs {Y} Closed Won', 'Opportunity', CW, OX + ' ; ' + OXP, 'StageName = Closed Won by New_Close_Date__c month (never CloseDate)', 'Month × year, optional split by Opp Created Year', f'Detail counts = summary ({OXP}, {OX})', 'O06', ''),
 (24, 'AWARENESS CAMPAIGN (section divider)', 'Divider: no data', '', '', '', '', '', '', '', ''),
 (25, f'{Q} REGIONAL AWARENESS CAMPAIGN', 'Display & video impressions, clicks, CPC, spend, conversions', '- (Google Ads)', '', '', '', '', '', '', 'Google Ads / agency cost-per-lead breakdown: not Salesforce'),
 (26, f'{Q} SALES STAGES (section divider)', 'Divider: no data', '', '', '', '', '', '', '', ''),
 (27, f'{Q} SALES PIPELINE BY STAGE MoM', 'Lead statuses by month; opp stages by month; CAC', 'Lead + Opportunity', L, OC + ' ; ' + OX + ' ; ' + OM + ' ; ' + CW, 'Lead Status by CreatedDate month, Is_MQL__c = TRUE (Not Aware = Needs Outreach, Working = Outreach Attempted). Opp StageName by CreatedDate month; Closed Won by New_Close_Date__c month. CAC = acquisition spend ÷ Closed Won count.', 'Month × Status / StageName', 'Status row totals = slide-12 MQLs by month; Closed Won row = slide 17', 'O09, O03, L11', 'Spend for CAC from agency worksheet'),
 (28, f'{Q} YoY PIPELINE OPPORTUNITY VALUE BY CHANNEL', f'Sales-owned: {PY} vs {Y} created opp $ by channel, all sources', 'Opportunity', OC + ' ; ' + OCP, DQ, 'Every opp created in the quarter, no lead join. SUM Amount by Lead_Category__c.', 'Lead_Category__c × year; normalize case (Organic → ORGANIC, Other → OTHER)', 'Grand total = slide-22 quarter totals', 'O01 (decide: show blank category as “No channel / direct-entered” or exclude), O02', ''),
]
F = Font(name='Arial', size=10); B = Font(name='Arial', size=10, bold=True); H = Font(name='Arial', size=10, bold=True, color='FFFFFF'); HF = PatternFill('solid', fgColor='1F3864')
DIV = PatternFill('solid', fgColor='E7E6E6'); EXT = PatternFill('solid', fgColor='FFF2CC')
wb = Workbook(); ws = wb.active; ws.title = 'Slide map'
ws.append(['Slide', 'Deck title', 'What the slide shows', 'Salesforce object', 'Primary export file', 'Supporting files', 'Filter / definition', 'Group by / fields', 'Cross-check', 'DQ flags to resolve', 'Non-Salesforce inputs'])
for c in ws[1]: c.font = H; c.fill = HF; c.alignment = Alignment(wrap_text=True, vertical='center')
for r in SLIDES:
    ws.append(list(r)); rr = ws.max_row
    for c in ws[rr]: c.font = F; c.alignment = Alignment(wrap_text=True, vertical='top')
    ws.cell(rr, 1).font = B
    if 'divider' in r[2]:
        for c in ws[rr]: c.fill = DIV
    if r[10] and not r[4]:
        for c in ws[rr]: c.fill = EXT
for i, w in enumerate([6, 34, 40, 14, 30, 36, 60, 50, 44, 48, 30], 1): ws.column_dimensions[get_column_letter(i)].width = w
ws.freeze_panes = 'C2'; ws.auto_filter.ref = ws.dimensions
fs = wb.create_sheet('Files')
fs.append(['File', 'Slides using it as primary', 'Slides using it as supporting', 'Slide list'])
for c in fs[1]: c.font = H; c.fill = HF
for f in [L, LP, OC, OX, OCP, OXP, LM, OM, CW, DQ, 'field_dictionary_Lead_Opportunity.csv']:
    fs.append([f]); rr = fs.max_row
    fs.cell(rr, 2).value = f"=COUNTIF('Slide map'!$E:$E,\"*\"&A{rr}&\"*\")"; fs.cell(rr, 3).value = f"=COUNTIF('Slide map'!$F:$F,\"*\"&A{rr}&\"*\")"
    fs.cell(rr, 4).value = ', '.join(str(r[0]) for r in SLIDES if f in (r[4] + ' ' + r[5]))
    for c in fs[rr]: c.font = F
for i, w in enumerate([48, 14, 14, 30], 1): fs.column_dimensions[get_column_letter(i)].width = w
p = f'{WD}/out/slide_to_report_map_{year}-Q{q}.xlsx'; wb.save(p); print('saved', p)
