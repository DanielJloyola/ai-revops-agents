# Exec Monthly Readout Agent

> Shown with illustrative data; company details removed.

## Problem
Leadership gets a monthly marketing and sales readout. Building it by hand meant pulling several Salesforce reports, pasting numbers into slides, and hoping nothing moved in between. Numbers often did move, because reps backfill statuses and close dates for days after month end, and two slides could disagree by one deal.

## How it works
- Claude pulls every Lead and Opportunity field for the month from Salesforce (read-only SOQL, `FIELDS(ALL)`, paged 200 rows at a time by Id).
- Three aggregate queries supply monthly trends back to January of the prior year, so month-over-month and year-over-year comparisons need no extra record pulls.
- Python scripts (`scripts/`) build the CSV pack, the MoM/YoY exec comparison table, a data-quality flag workbook, and, when a deck is supplied, a corrected slide plus a highlighted review copy.
- Month windows are bucketed in Eastern time to match how the org's reports run.

## Guardrails
- **Hard abort on dataset-vs-aggregate mismatch.** If the paged record count for a dataset disagrees with its aggregate count, or any Id appears twice across pages, the build stops. That catches a missing page or data that changed mid-pull, so a wrong number never reaches an exec.
- **Data-quality flag workbook.** 28 lead and opportunity checks (blank reasons, backdated closes, future close dates, attribution gaps), one row per record per flag, summarized with COUNTIF formulas.
- **Live, and labeled as live.** Every file is stamped with the UTC pull time. This is the live counterpart to the quarterly recap agent, which uses frozen static exports; the two are never mixed.
- **Every mismatch gets a name.** Deck-vs-live gaps are bridged to a specific record (via `LastModifiedDate`), never "close enough".
- Known traps (unreliable historical flags, migration-inflated months) are footnoted automatically.

## Result
A repeatable monthly pack that ties out to Salesforce reports, ships with an Excel workbook behind every number, and turns slide verification into a scripted check instead of a manual hunt.

## Files
- `SKILL.md`: the agent's instructions
- `scripts/`: `readout_month.py`, `ingest.py`, `build_exports.py`, `build_dq.py`, `slide_patch.py`, `common.py`
- `references/`: data-quality flags, attribution rule, slide map, deliverable spec
