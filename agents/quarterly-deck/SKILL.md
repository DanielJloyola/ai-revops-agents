---
name: "quarterly-marketing-recap-data"
description: Builds the static Salesforce data pack behind a quarterly Marketing Recap deck (marketing results, YoY, and sales-stage slides). Pulls every Lead and Opportunity field for the quarter and the same quarter a year earlier as frozen CSV exports, then builds monthly summaries, a data-quality flag workbook, a slide-to-report map, and the path (form fills to MQLs to Net MQLs to SQLs) pivot workbook with an editable PowerPoint chart slide. Use for marketing recap, quarterly recap data, static Salesforce data for the recap, or rebuilding the path slide. Static exports only; never quote live Salesforce numbers for this deck.
---

# Quarterly Marketing Recap: static Salesforce pull

> Portfolio version by Daniel Jay Loyola. Company details removed ("Acme Health" is a placeholder).
> **All figures are illustrative; the production version pins real check figures.**

The rule for this deck: **every number comes from a frozen export taken on one date**, never from a live query re-run later. The job is to take that snapshot, tie it out, and hand back files the slides can be built from. Deliver finished files plus a short readout, not a tutorial.

Read `../salesforce-assistant/SKILL.md` first if available; it holds the org definitions. The definitions below repeat only what the scripts depend on.

## Inputs

- **Quarter**: from the deck title, the request, or the current date (for example `2026-Q3`). Confirm it in one line if it is not explicit.
- **Prior-year comparison quarter**: same quarter one year earlier, always pulled.
- Optional: the deck `.pptx`, read with the pptx skill's `slide_text.py`.

Connector: the read-only Salesforce tools. Only `soqlQuery` and `getObjectSchema` are needed.

## Procedure

Work in `/home/claude/recap/<quarter>/` with `pages/` and `out/` underneath. Script paths are relative to this skill directory; every script prints what it did.

1. **Windows and queries.** `python scripts/recap_quarter.py 2026-Q3` prints the date windows and exact SOQL. Datasets (all `SELECT FIELDS(ALL) ... ORDER BY Id LIMIT 200`): `lead_<q>`, `lead_<pq>` (prior-year quarter), `opp_created_<q>`, `opp_created_<pq>`, `opp_closed_<q>`, `opp_closed_<pq>` (IsClosed = true and `New_Close_Date__c` in the quarter, any created year). It also prints three aggregate queries covering January of the prior year to today.

2. **Schema.** Call `getObjectSchema` with `Lead,Opportunity` and pass the result path to `python scripts/ingest.py schema <path>`.

3. **Page through each dataset.** `FIELDS(ALL)` is capped at 200 rows per call. Run the query, then `python scripts/ingest.py <dataset> <tool_result_path>`; re-run with `AND Id > '<lastId>'` before `ORDER BY` until a page returns fewer than 200 rows. Warn the user before a long migration-heavy pull.
   - Never retype an inline result. Re-run it combined with another query so it lands on disk and split it with `--filter`, or write aggregate JSON verbatim to `pages/agg_<name>.json`.

4. **Build the pack.** `python scripts/build_exports.py 2026-Q3` writes the six `<dataset>_ALLFIELDS_<pulldate>.csv` files, monthly summaries, the field dictionary, and a README with definitions, row counts, and tie-out. **It aborts if any page has duplicate Ids or a dataset's row count disagrees with the aggregate query.**

5. **Data-quality workbook.** `python scripts/build_dq.py 2026-Q3` writes `out/data_quality_flags_<pulldate>.xlsx` (Summary tab of COUNTIF formulas, one tab per dataset). Flags in `references/dq_flags.md`. Recalculate with zero formula errors.

6. **Slide map.** `python scripts/build_slide_map.py 2026-Q3` writes `out/slide_to_report_map_<quarter>.xlsx`: which file, filter, group-by, cross-check, and DQ flags feed each slide. See `references/slide_map.md`.

7. **Path slide.** `python scripts/build_path_pivot.py 2026-Q3` writes `out/slide_path_detail_and_pivot.xlsx` (pivot overview built from COUNTIFS, MQL dimensions, detail) and `out/path_numbers.json`. Then `node scripts/build_path_slide.js 2026-Q3` writes `out/Path_FormFills_MQLs_SQLs.pptx`, one slide with four native, editable line charts. Validate and render it for a visual check.

8. **Deliver.** Zip `out/` and present the zip plus the workbooks and the pptx. Readout: a table of file, definition, and rows; the tie-out numbers; and the two or three DQ flags that change a slide. Never announce the numbers as "current"; they are the snapshot of the pull date.

## Definitions the scripts rely on

| Measure | Filter |
| --- | --- |
| Form fills / leads | every Lead with CreatedDate in the quarter (Eastern time months) |
| MQLs | `Is_MQL__c = true` |
| Net MQLs | `Is_MQL__c = true AND Net_MQL__c = true` |
| SQLs | `Is_MQL__c = true AND Status = 'Qualified'` |
| Channel on the path slide | `Lead_Category__c`: ORGANIC, PAID, DIRECT, AI SEARCH; REFERRAL + DRIP CAMPAIGN + UNKNOWN roll into OTHER |
| Created pipeline | Opportunity `Amount` by month of `CreatedDate`, all stages, all sources |
| Closed Won | `StageName = 'Closed Won'` by month of `New_Close_Date__c` (never standard CloseDate) |
| Lost | `StageName IN ('Lost Opportunity','Closed Lost')` by month of `CreatedDate` |

Months are bucketed in America/New_York because that is how the org's reports run; `CreatedDate` arrives in UTC and a few leads move months if bucketed raw. Say which you used.

## Lessons learned

- Net MQL is unreliable before the framework's deployment year (not backfilled). Never show a prior-year Net MQL comparison; compare leads, MQLs, and converted MQLs.
- Prior-year lead volume can include a one-time migration batch; footnote it on YoY slides.
- Picklist values change between quarters; use the values in the export.
- About a third of opportunities created in a quarter have no `Lead_Category__c` (created on the account). They belong in the total-opportunities scope; the slide map says which slide uses which scope.
- **The pull date is frozen for the whole readout.** If a join reaches a record outside the frozen files (for example a SQL whose converted opp was created after quarter end), exclude it, keep it visible in the detail tab marked EXCLUDED with the reason, and state the count and dollars in the readout. Do not fetch it to "complete" the number.
- Spend and awareness-campaign data are not in Salesforce; leave those cells for the agency worksheet.
