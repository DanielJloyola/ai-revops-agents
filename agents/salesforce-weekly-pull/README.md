# Salesforce Weekly Pull

Shown with illustrative data; company details removed.

## Problem
Every Monday the weekly reporting cycle started with exporting eight Salesforce reports by hand, renaming them, and dropping them into a dated folder. Slow, and the manual exports used inconsistent date windows.

## How it works
- Computes the reporting window (last complete Monday-to-Sunday, Eastern time) and the exact SOQL for each report.
- Runs each query through a read-only Salesforce connector, paging past the 2,000-row limit by Id.
- Converts the raw JSON into CSVs that match the manual-export layout byte for byte where the downstream scripts care: picklist labels, name formats, date formats, encodings.
- Writes them into the dated week folder without ever overwriting a manual export.

## Guardrails
- Row-count checks: each extract is compared against a SOQL COUNT query; 4 of 7 extracts must match exactly, the rest have documented formulas.
- Date-window checks on every dated column and label checks on picklist values.
- Week-over-week drift check flags any file whose row count moved by more than 50%.
- Read-only by design; never edits a query's fields or filters; known differences from the manual reports are reported, not silently "fixed".

## Result
The manual export step is gone. The pull feeds the weekly reporting pipeline, which as a whole turned an 8+ hour weekly task into about 2 minutes.
