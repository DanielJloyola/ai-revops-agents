# Weekly Reports Runner

Shown with illustrative data; company details removed.

## Problem
Weekly C-suite and Board reporting meant four separate builds (Red Green Report, Weekly Board, Weekly Ops Report, monthly SCR) from Salesforce and billing-system exports, with paths, dates and inputs hand-edited every week. It took a full working day and the numbers had to tie across reports.

## How it works
- Phase 1 (prep/draft): computes the reporting week, builds the folder structure, checks every input file and its date range, pulls missing Salesforce extracts, updates script configs, runs the Red Green DRAFT and diffs it against last week's final.
- Human proof gate: stops and waits for the owner to review, assign agency codes and make keep/exclude calls.
- Phase 2 (final): applies the decisions, runs Red Green FINAL, the Board, Ops with styling, and the monthly SCR report, then writes a readout.

## Guardrails
- Hard stop for human review before anything goes final.
- Tie-out checks: Board Row 17 must equal Red Green Row 17 exactly; Ops Closed Won and MQLs must tie to the Board.
- Never reuses an agency code already assigned elsewhere; flags clashes instead.
- Refuses to substitute last week's data for a missing input; runs only against the current week's folder.
- Outputs stay local; nothing is emailed or uploaded automatically.

## Result
Turned an 8+ hour weekly reporting task into about 2 minutes of run time plus a focused human review, with cross-report tie-outs checked every week.
