# Quarterly Marketing Recap Data Agent

> Shown with illustrative data; company details removed.

## Problem
The quarterly Marketing Recap deck runs to 18 data slides (funnel path, unqualified and lost reasons, channel revenue, ROAS/MER, YoY pipeline, sales stages). Built by hand from live reports, numbers shifted between slides as the org changed, and nobody could say which report fed which number.

## How it works
- Claude pulls every Lead and Opportunity field for the quarter and the same quarter a year earlier (read-only SOQL, `FIELDS(ALL)`, paged by Id) and freezes them as CSV exports on one pull date.
- Python scripts (`scripts/`) build monthly summaries, a data-quality flag workbook, a slide-to-report map, and the path pivot workbook (form fills to MQLs to Net MQLs to SQLs, every cell a COUNTIFS formula over the detail tab).
- A Node script (`build_path_slide.js`, pptxgenjs) renders the path slide as four native, editable PowerPoint line charts.

## Guardrails
- **Hard abort on dataset-vs-aggregate mismatch.** Paged row counts must equal the aggregate query, and no Id may appear twice; otherwise the build stops.
- **Static exports only.** Every slide number comes from one frozen pull. Records outside the snapshot are excluded and listed as EXCLUDED with a reason, never fetched live to "complete" a number. The monthly exec readout agent is the live counterpart; the two are never mixed.
- **Data-quality flag workbook.** 27 lead and opportunity checks with COUNTIF summaries, so the flags that change a slide are visible before the deck ships.
- **Slide-to-report map.** Each slide lists its source file, filter, group-by, cross-check, and DQ flags, so any number can be traced.

## Result
A quarterly recap where every slide traces to a named export, filter, and cross-check, and the path slide rebuilds itself from data instead of hand-edited charts.

## Files
- `SKILL.md`: the agent's instructions
- `scripts/`: `recap_quarter.py`, `ingest.py`, `build_exports.py`, `build_dq.py`, `build_slide_map.py`, `build_path_pivot.py`, `build_path_slide.js`, `common.py`
- `references/`: data-quality flags, slide map
