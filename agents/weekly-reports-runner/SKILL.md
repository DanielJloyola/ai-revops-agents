---
name: weekly-reports-runner
description: Runs the weekly reporting cycle for the Red Green Report, Weekly Board, Weekly Ops Report and (at month start) the SCR Report. Two phases. "Prep/draft" builds the week folder, pulls or checks inputs, updates the scripts and produces the Red Green DRAFT, then stops for a human proof. "Final" applies the reviewer's codes and runs Red Green FINAL, the Board, Ops with styling and SCR, with tie-out checks. Does not run the lead readout.
---

# Weekly reports runner (Red Green · Board · Ops · SCR)

All figures in this file are illustrative; the production version pins real check figures.

Built by Daniel Loyola (RevOps) for Acme Health, a fictional multi-state occupational health screening company. You do the technical work and give the owner a short readout. The procedure, sources and gotchas are documented in `Weekly Reporting/WEEKLY_REPORTING_SOURCES_AND_AUTOMATION.md` and the tick list `Weekly Reporting - Checklist (Board, Ops, Red Green, SCR).xlsx`. Read the documentation first if anything here is unclear.

## Config

```
WEEKLY  = "<reporting-folder>/Weekly Reporting"
SCRIPTS = WEEKLY + "/Scripts"
PYTHON  = "<reporting-folder>/.venv/bin/python"
PULL    = SCRIPTS + "/Salesforce Pull"          # sf_week.py, sf_pull_to_csv.py (Salesforce connector pull)
MEMORY  = "<memory-folder>"                      # pending-agency-codes.md = pending agency codes
```
Week folder = `WEEKLY/<Month YYYY>/<MM.DD.YY>/` where MM.DD.YY is the Monday after the reporting week; sub-folders `Salesforce Reports/`, `Billing Reports/`, `Prior Week Reporting/`, `This Week Reports/`. Folder names have drifted in the past, so look before you edit paths.

## HARD RULES
1. **Red Green proof gate.** Build the DRAFT, report the review points, then STOP. Only run MODE = final after the owner explicitly OKs the draft. If the answer has codes and decisions but no literal OK, say you are treating that as the OK and proceed only if the review is clearly finished.
2. **Current-week folder only.** Compute the week from today's date (`PYTHON PULL/sf_week.py` prints WS, WE, WEEK_TAG, MONTH_FOLDER). Never run against last week's folder.
3. **Never apply an agency code that is already used by another opportunity** without flagging the clash; the rule is "if it's already in use, don't apply it".
4. Keep the PERSISTENT Ops exclusion (`Client A - RFT`); clear one-off entries and `REASSIGN_MQL_OWNER` each week.
5. Outputs go to `This Week Reports/`. Do not email, upload or move files to shared drives.

## Phase 1: prep and draft

1. Week + folder: run `sf_week.py`, create the week folder and the four sub-folders if missing. State the window in one line.
2. Inputs: check the checklist files. Required for this phase: `Billing Reports/SCR YTD.csv`, `SCR Rolling YTD.csv`, `SCR WTD.csv`, `VolumeVisitReport*.csv`, the dashboard PNG in `Salesforce Reports/`, and last week's three finals (copy them from last week's `This Week Reports/` into `Prior Week Reporting/` if the owner has not). If the six Salesforce CSVs are absent, pull them with the `salesforce-weekly-pull` procedure (window + queries from `sf_week.py`, convert with `sf_pull_to_csv.py`). If a billing-system file is missing, list what is missing and stop; do not substitute last week's.
   - Billing periods expected: SCR YTD 01/01 → run Monday; SCR Rolling 1st of the month 12 months back → run Monday; SCR WTD prior Monday → run Monday; Visit Volume prior Mon → Sun. Read the `Date Range:` cell in row 2 of each CSV and flag any that look wrong.
3. Script config (edit with Python string replacement, then grep to confirm):
   - `Red Green Report/red_green_report.py`: MODE='draft', REPORT_DATE, PREV_SHEET='Red Green Report <prev tag>', BASE_DIR, OUT_DIR, PREV_XLSX (prior FINAL in Prior Week Reporting), RG_CSV (this week's Master RG csv name), REVIEWED_XLSX / OUTPUT_DRAFT / OUTPUT_FINAL with this week's tag.
   - `Weekly Board Metrics/weekly_board_builder.py`: BASE_DIR, OUT_DIR, INPUT_BOARD (prior Board), OUTPUT_BOARD, RED_GREEN_FILE (this week's FINAL name), NEW_TAB_DATE, WEEK_START, WEEK_END.
   - `Ops closed & created Last 7 Report/generate_weekly_report.py`: BASE_DIR, OUT_DIR, TEMPLATE_XLSX (last week's ops xlsx), the Opps Closed / Created / Activities / Leads file names, exclusions per rule 4.
4. Run Red Green DRAFT: `PYTHON red_green_report.py`. Then compare the draft tab to the prior FINAL tab with pandas and report, in short tables: rows and ON TRACK/BEHIND vs last week; new opps (name, amount, owner, agency code present or not); status changes; dropped opps; the REVIEW rows; the standing no-code reminders from `MEMORY/pending-agency-codes.md` (check each still has no code; drop any that now has one; add the new codeless opps with today's date).
5. STOP. Ask the owner to proof and to give codes / keep-exclude calls.

## Phase 2: final, Board, Ops, SCR

6. Apply the owner's answers to the draft workbook with openpyxl (Agency Code column; set `Keep or Exclude?` from REVIEW to Keep/Exclude as told). Before applying a code, check it is not already on another opp in the draft, the prior FINAL, or a different account in `Billing Reports/AgencyAcctProjectMgr.csv`; if it is, leave blank and say so. Update the pending-codes memory file.
7. Set MODE='final', run. Capture `Row 17 SCR-verified`. If it prints $0.00 or 0 rows, the Type/Stage values changed; investigate (the script accepts "New" and "New Business").
8. Board: read the dashboard PNG and fill `NEW_VALUES` (WTD stage bars, NCD WTD, Total Leads and MQL donuts, YTD and prior-FY stage totals; ex-upsell YTD = Closed Won YTD minus last known upsell unless the owner gives the real figure). Run `weekly_board_builder.py`. Check the printed Board Row 17 equals the Red Green Row 17 exactly; if not, find the opp whose agency vs onsite SCR differ.
9. Ops: run `generate_weekly_report.py`, then `color_wow_warnings.py "<ops.xlsx>"` and `border_dashboard.py "<ops.xlsx>"`. Read the Dashboard tab and check Closed Won WTD and MQL leads tie to the Board's NCD WTD and MQL numbers. Flag any Stage-leak drops the script prints and any large closed-won item that is a resell or old opp.
10. SCR (only if this is the first run of a calendar month): copy the newest `SalespersonCommissionReport*.csv` from Downloads into `Billing Reports/`, run `Monthly SCR Report/build_scr.py --scr <that csv> --lookup "Billing Reports/AgencyAcctProjectMgr.csv" --out "This Week Reports"`, and report the grand total and period.
11. Readout: window; table of output files; RG rows / on-track / behind / Row 17; Board Row 17 and Row 26; Ops CW, opps created, pipeline, MQLs, activities; tie-out results; anomalies; reminders carried to next week. Then update the memory notes (run log, pending codes) and stop.

## If corrected lead statuses arrive later in the week
Make a refreshed copy of the Leads export with the corrected statuses, point the Ops script at it, re-run Ops plus the two styling scripts, keep the web-form inbox user excluded from engagement metrics, and re-add the Needs Outreach Follow-Up block for the prior snapshot's leads. Back up the previous Ops file first.

## Standing facts
- Reps: an MQL team of three reps (Rep A, Rep B, Rep C) and two strategic account managers (Rep D, Rep E); the web-form inbox user is a routing catch-all, never a rep.
- Board Row 17 / RG Row 17 use max(agency SCR, onsite SCR). Board ex-upsell YTD may be an estimate; ask for the real "No Upsell" figure when convenient.
- The pending codes list lives in `MEMORY/pending-agency-codes.md`; read it every draft, update it every final.
