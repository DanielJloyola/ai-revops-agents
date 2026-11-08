---
name: salesforce-weekly-pull
description: Pulls the weekly Salesforce report extracts (Leads Last 7 Days, Opportunities Created / Closed Past 7 Days, Activities Last 7 Days, Master Red Green Report, Total Leads FY, YTD Velocity to Closed Won) directly from Salesforce through a read-only connector for the prior Monday-to-Sunday week, and writes them as the CSV files the weekly reporting scripts expect. Replaces exporting reports by hand at the start of the weekly reporting cycle. It does not pull Contacts, does not touch billing-system or HubSpot files, and does not run the report builders.
---

# Salesforce weekly pull

All figures in this file are illustrative; the production version pins real check figures.

You replace the manual "export 8 Salesforce reports and drop them in the week folder" step of the weekly reporting cycle at Acme Health (a fictional multi-state occupational health screening company). You read from Salesforce only (the connector is read-only) and write CSV files locally. The owner (Daniel Loyola, RevOps) prefers a finished result plus a short readout.

## Config (edit if the machine or folders change)

```
PULL_DIR   = "<reporting-folder>/Weekly Reporting/Scripts/Salesforce Pull"
WEEKLY_DIR = "<reporting-folder>/Weekly Reporting"      # <Month YYYY>/<MM.DD.YY>/Salesforce Reports/
PYTHON     = "<reporting-folder>/.venv/bin/python"
```
Helper scripts in PULL_DIR: `sf_week.py` (week window + exact SOQL per report), `sf_pull_to_csv.py` (connector JSON -> CSV in the manual-export layout), `sf_refresh_sidefiles.py` (rebuild picklist-label and user-name side files). Read `WEEKLY_SALESFORCE_PULL_RUNBOOK.md` there if anything is unclear. (Helper scripts are not included in this portfolio copy.)

## Procedure

1. **Window.** Run `PYTHON sf_week.py` (add `--week-end YYYY-MM-DD` to target a specific Sunday). It prints JSON with `window` (WS Monday, WE Sunday, WEEK_TAG such as `MM.DD.YY`, MONTH_FOLDER), `queries` and `counts`. The reporting week is always the last complete Monday-Sunday in America/New_York. Create `WEEKLY_DIR/<MONTH_FOLDER>/<WEEK_TAG>/Salesforce Reports/` if it does not exist. State the window in one line before pulling.

2. **Pull.** For every entry in `queries`, call the Salesforce connector's SOQL tool with the query text exactly as printed. `leadsfy` is a list (one query per month); run each. Result handling:
   - Large results are saved by the harness to a file whose path is in the tool result. Record that path.
   - Small results come back inline. Write the whole JSON object (`{"totalSize":..,"done":..,"records":[...]}`) to `<scratchpad>/<key>.json` verbatim.
   - If a result says `"done": false`, the connector truncated it (2,000 rows per call, fewer for very wide rows). Take the last record's `Id`, re-run the same query with ` AND Id > '<lastId>'` inserted before `ORDER BY`, and keep going until `done` is true. Pass all pieces to the converter.
   - Never edit a query's field list or filters; if Salesforce rejects a field, stop and report it.

3. **Convert.** Run the converter once per report, listing every result file for that report:
   ```
   PYTHON sf_pull_to_csv.py --report leads7   --json <files> --out "<week>/Salesforce Reports/Leads Last 7 Days-<WE>.csv"
   PYTHON sf_pull_to_csv.py --report created7 --json <files> --out "<week>/Salesforce Reports/Opportunities Created Past 7 Days-<WE>.csv"
   PYTHON sf_pull_to_csv.py --report closed7  --json <files> --out "<week>/Salesforce Reports/Opportunities Closed Past 7 Days-<WE>.csv"
   PYTHON sf_pull_to_csv.py --report acts     --json <task files> <event files> --out "<week>/Salesforce Reports/Activities Last 7 Days-<WE>.csv"
   PYTHON sf_pull_to_csv.py --report rg       --json <files> --out "<week>/Salesforce Reports/Master - Red Green Report-<WE>.csv"
   PYTHON sf_pull_to_csv.py --report velocity --json <velocity_opps file> <velocity_hist file> --out "<week>/Salesforce Reports/YTD Velocity to Closed Won.csv"
   PYTHON sf_pull_to_csv.py --report leadsfy  --json <all monthly files> --out "<week>/Salesforce Reports/Total Leads FY <FY>.csv"
   ```
   `<WE>` is the Sunday date (YYYY-MM-DD). Never overwrite a manual export already placed in the folder; if a same-named file exists, write yours with a ` (auto)` suffix and say so.

4. **Verify** before reporting. Run each query in `counts` and compare with the CSV row counts: leads7, created7, closed7 and rg must match exactly (4 of 7 extracts enforced row for row); acts = tasks count + events; leadsfy = COUNT. Also check with Python that Created Date / New Close Date / Date columns fall inside WS..WE, that Lead Status values are labels (e.g. "Needs Outreach", never "Not Aware"), and that rep full names (with middle names where the report shows them) appear in Lead Owner / Assigned columns. If last week's folder has the same files, compare row counts and flag anything that moved by more than 50%.

5. **Report back** with the window, a table of file -> rows, the count checks, and any anomaly. Then stop. Do not run the Red Green, Board, Ops or lead readout scripts, and do not update their path constants unless asked; just give the file names so the weekly run can point at them.

## Rules the owner set

- Window is the prior Monday-to-Sunday, Eastern time, for everything dated by the week. (The old manual exports were slightly different: leads ran Sunday-Saturday, activities Tuesday-Monday; the automated pull is the correct Monday-Sunday.)
- Only Salesforce is automated for now, and NOT the Contacts export, which the owner exports himself. Billing-system reports, HubSpot, the dashboard PNG and prior-week finals are also supplied by the owner. If Contacts is ever automated, the converter's `contacts` report and the seeded master in `PULL_DIR/master/` still work; re-enable the query in sf_week.py.
- Reports are read from Salesforce, never written to it.

## How each report is defined (reverse-engineered from the manual exports)

| File | Salesforce definition used |
|---|---|
| Leads Last 7 Days | Lead.CreatedDate in window |
| Opportunities Created Past 7 Days | Opportunity.CreatedDate in window |
| Opportunities Closed Past 7 Days | Opportunity.New_Close_Date__c in window (any stage; the Ops script keeps Closed Won) |
| Activities Last 7 Days | Task: ActivityDate in window and Status = Completed; Event: ActivityDate in window |
| Master - Red Green Report | Opportunity StageName = Closed Won and Months_Since_Closed__c <= 12 (rolling 12 months) |
| YTD Velocity to Closed Won | Opportunities created this FY in Closed Won / Lost Opportunity / Closed Lost, joined to their StageName field-history rows; one row per stage change; opps with no stage history are excluded, as in the manual report |
| Total Leads FY | Leads created this FY, about 44 columns the scripts use; long-text attribution columns left blank; "Is MQL?" here is the converted opportunity's flag |

## Things the converter already handles (do not re-implement)

Picklist API values -> report labels (Lead Status "Not Aware" -> "Needs Outreach", Type "New" -> "New Business", legacy lead-size values -> their "(Legacy)" labels); full names with middle name on Lead Owner / Assigned / Edited By only; multi-select fields sorted alphabetically joined with "; "; dates as M/D/YYYY Eastern; booleans as 1/0; amounts with two decimals; latin-1 with quoted fields for the five weekly files, UTF-8 for the three year-to-date files. If a label or rep name looks wrong, refresh the side files: run the `users` query and `PYTHON sf_refresh_sidefiles.py --users <file>`; run getObjectSchema for Lead, Opportunity, Task, Event, Contact, Account and `--schemas <files>`.

## Known differences from the manual exports (report them, do not "fix")

- Total Leads FY: the manual report omitted a small number of leads (about 1%) created this year that carry no visible distinguishing attribute; the pull includes them.
- Activities: the manual report also dropped tasks owned by the admin user; the pull keeps them (the Ops script filters to sales reps anyway).
- Long text columns on Total Leads (referring sites, UTM, notes, "How can we help?") are blank because pulling them cuts the connector to 200 rows per call; no weekly script reads them.
