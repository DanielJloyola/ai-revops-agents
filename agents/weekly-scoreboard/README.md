# Weekly Sales Scoreboard

Shown with illustrative data; company details removed.

## Problem
The Sales Director runs a weekly sales competition: reps earn points for pipeline movement logged in Salesforce on one day. Building the scoreboard meant exporting three reports by hand, cleaning grouped exports, scoring every lead and opportunity change against a points scheme, and writing up the judgment calls.

## How it works
- Picks the target competition day automatically and builds an exact UTC window that matches the Eastern-time report filters (including daylight-saving changes).
- Pulls three datasets with read-only SOQL: lead status history, opportunity stage history (derived From/To stages from stage snapshots), and meetings/activity.
- Scores every change with explicit rules: who gets credit (the person who logged the change), skipped-stage sums, same-day reversals, excluded meeting types.
- Builds a formula-driven Excel workbook: ranked Scoreboard, Decisions for the Sales Director, per-rep Playbook written against each rep's open pipeline, plus the raw source tabs.

## Guardrails
- Reconciliation: the first Salesforce-fed run reproduced the three manual exports row for row.
- Every readout states the row count of each pull so it can be checked against the reports.
- Hand-tally of each rep from the source tabs must equal the Calc tab; ship only at zero formula errors.
- Judgment calls and overrides are never silent: each one is written on the Decisions tab, and open rulings carry forward week to week.
- Admin test edits are filtered out and disclosed.

## Result
Scores 5 to 6 reps weekly with no manual report exports; the Sales Director gets a ranked scoreboard, the reasoning behind every close call, and a next-week playbook per rep.
