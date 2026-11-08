---
name: "exec-monthly-readout"
description: Pulls a live Salesforce data pack for an executive monthly marketing and sales readout, defaulting to the previous calendar month. Pulls every Lead and Opportunity field for the readout month plus monthly aggregate trends, then builds the month-over-month and year-over-year comparison table, monthly summaries, and a data-quality flag workbook, all stamped with the pull time. Use for exec readout, monthly readout, monthly numbers for leadership, or refreshing the readout data. This is the live counterpart to the quarterly recap skill; never mix its numbers into the static quarterly deck.
---

# Exec Monthly Readout: live Salesforce pull

> Portfolio version by Daniel Jay Loyola. Company details removed ("Acme Health" is a placeholder).
> **All figures are illustrative; the production version pins real check figures.**

The opposite rule from the quarterly recap: **every run pulls fresh from Salesforce, and every number is the state of the org at the pull timestamp.** Numbers drift between runs because formula fields (Is MQL?, Net MQL) evaluate live and reps backfill MQL flags, reasons, and New Close Dates for days after month end. Stamp everything with the pull time (UTC), say so in the readout, and re-pull before the exec meeting rather than reusing an old pack. The user is a RevOps analyst; deliver finished files plus a short readout, not a tutorial.

Read `../salesforce-assistant/SKILL.md` first if available. It holds the org definitions (Is MQL?, Net MQL, SQL, the New Close Date rule, status API values, the migration caveat). The definitions below repeat only what the scripts depend on.

## Inputs

- **Month**: defaults to the **previous calendar month**. Accepts `2026-10` to override. Confirm the month in one line before pulling.
- **Comparisons**: MoM (prior month) and YoY (same month prior year) come from the aggregate queries, with no extra record pulls. Record-level detail for a comparison month is optional (`--with prior_month,prior_year`); only pull it if a slide needs it, and warn first for migration-heavy months.
- Optional: the exec deck `.pptx`, read with the pptx skill's `slide_text.py`.

Connector: the read-only Salesforce tools. Only `soqlQuery` and `getObjectSchema` are needed.

## Procedure

Work in `/home/claude/readout/<YYYY-MM>/` with `pages/` and `out/` underneath. Start every run with `rm -rf /home/claude/readout` so leftover pages from an earlier run are not ingested. Script paths are relative to this skill directory; every script prints what it did.

1. **Windows and queries.** `python scripts/readout_month.py` (no argument = previous month) prints the date window and the exact SOQL. Datasets (all `SELECT FIELDS(ALL) ... ORDER BY Id LIMIT 200`): `lead_<ym>`, `opp_created_<ym>`, `opp_closed_<ym>` (IsClosed = true and `New_Close_Date__c` in the month, any created year). It also prints count-check queries and three aggregate queries (lead monthly with Net MQL, opp created monthly by stage, closed won monthly by New Close Date) from January of the prior year to today. These feed the MoM/YoY table.

2. **Schema** (optional; first run or when fields change). Call `getObjectSchema` with `Lead,Opportunity` and pass the result path to `python scripts/ingest.py schema <path>`.

3. **Page through each dataset.** `FIELDS(ALL)` is capped at 200 rows per call, so loop: run the query, then `python scripts/ingest.py <dataset> <tool_result_path>`; it saves the page and prints `lastId`. Re-run with `AND Id > '<lastId>'` before `ORDER BY` until a page returns fewer than 200 rows.
   - A small result may come back inline instead of on disk. Never retype it. Re-run it combined with another query so it exceeds the inline size and split it with `ingest.py --filter`, or write aggregate JSON verbatim to `pages/agg_<name>.json`.
   - **Pull everything in one sitting.** A live org changes under you; if the pull spans hours, the aggregate cross-checks can legitimately fail. Re-pull rather than patch.

4. **Build the pack.** `python scripts/build_exports.py` writes to `out/`:
   - `<dataset>_ALLFIELDS_<pullstamp>.csv` (compound address fields flattened)
   - `exec_comparison_<month>_<pullstamp>.csv`: Leads, MQLs, Net MQLs, Converted MQLs, SQL Count, Opps created, Created pipeline $, Closed Won # and $ (New Close Date) across readout month, prior month, MoM, same month prior year, YoY, with Net MQL and migration footnotes applied automatically
   - monthly summary CSVs and an optional field dictionary
   - `README_<month>_exec_readout.md` with the pull stamp, live-data caveat, definitions, row counts, tie-out, and the comparison table
   **It aborts if any page has duplicate Ids or a dataset's row count disagrees with its aggregate** (missing page, or data moved mid-pull: re-pull).

5. **Data-quality workbook.** `python scripts/build_dq.py` writes `out/data_quality_flags_<pullstamp>.xlsx`: Summary tab of COUNTIF formulas, one tab per dataset, one row per record per flag. Flags are listed in `references/dq_flags.md`. Recalculate with the xlsx skill's `recalc.py`; zero formula errors required.

6. **Slide verification.** Read `references/deliverables.md` first. Every verification returns a PowerPoint (clean copy plus highlighted review copy, via `scripts/slide_patch.py`) **and** an Excel workbook. `references/slide_map.md` maps each slide to its dataset, filter, and cross-check. When a deck is supplied, verify slide by slide and write `out/VERIFICATION_<month>_deck_vs_live_<pullstamp>.md`: exact matches marked, every mismatch bridged to a named record or a post-pull change, never "close enough".

7. **Deliver.** Always include an Excel workbook with any numbers or updated slides. Zip `out/`, then present the zip plus the comparison CSV and DQ workbook. Readout: lead with the pull timestamp, then the MoM/YoY table, the tie-out line, and the two or three DQ flags that would change an exec number. In the first week of a month, say that prior-month numbers are still settling and recommend a re-pull on the day of the readout.

## Definitions the scripts rely on

| Measure | Filter |
| --- | --- |
| Form fills / leads | every Lead with CreatedDate in the month |
| MQLs | `Is_MQL__c = true` |
| Net MQLs | `Is_MQL__c = true AND Net_MQL__c = true` |
| SQLs | `Is_MQL__c = true AND Status = 'Qualified'` (detail); `SUM(SQL_Count__c)` in the monthly trend |
| Channel | `Lead_Category__c`: ORGANIC, PAID, DIRECT, AI SEARCH; REFERRAL + DRIP CAMPAIGN + UNKNOWN roll into OTHER |
| Created pipeline | Opportunity `Amount` by month of `CreatedDate`, all stages, all sources |
| Closed Won | `StageName = 'Closed Won'` by month of `New_Close_Date__c` (never standard CloseDate) |
| Lost | `StageName IN ('Lost Opportunity','Closed Lost')` by month of `CreatedDate` |

Month windows and aggregates are **Eastern-time bucketed** to match the org's reports: detail queries use ET-midnight UTC boundaries from `et_window()`, and the CreatedDate aggregates use `convertTimezone()`. Validate once per run that the readout month's aggregate count equals the ET count check (for example 450 vs 452 raw UTC). A mismatch means the connector user's time zone is not Eastern; the explicit ET windows are then the source of truth.

## Lessons learned

- **Live means it moves.** A pull on the 2nd understates the prior month. Always state the pull stamp; never present two pulls as one dataset.
- **Never feed these numbers into the quarterly recap deck,** which is frozen-export-only.
- Net MQL is unreliable before the framework's deployment year (not backfilled). The comparison table suppresses it automatically.
- Prior-year lead volume can include a one-time data migration; the table footnotes YoY leads and MQLs for those months.
- Picklist values change over time; use the values in the export, not last month's labels.
- About a third of opportunities created in a month have no `Lead_Category__c` (created directly on the account). They belong in the total-opportunities scope, not lead-based channel views.
- **SQL opp amounts on lead slides include converted opps created after month end.** Join on `ConvertedOpportunityId` and fetch converted opps outside the month by Id; do not drop them. Count conversions with no opp at $0.
- **Two closed-won scopes:** all-in (Closed Won by New Close Date in month, any created period) and marketing-attributed (all-in minus deals on accounts with no marketing tie). See `references/attribution.md`.
- **Paid campaign slides group by `UTM_Campaign__c`.** Similar-looking fields from other tools are empty; the wrong column reads 100% untagged. Split true untagged by `GCLID__c` presence.
- Lead Category is a formula, so a lead can switch channels between pulls when its UTM or GCLID inputs are edited. Bridge channel deltas before calling them errors.
- **Bridging drift:** for any deck-vs-live gap, query the month's records with `LastModifiedDate >=` the deck's pull date; it names the moved record nearly every time.
- **One deck, one pull.** Pulling different slides at different times puts two bases in one deck (a single mid-day conversion was enough to make two slides disagree).
- Spend, agency fees, and anything from the marketing automation or billing systems are not in Salesforce; leave those cells for the user's worksheets.
