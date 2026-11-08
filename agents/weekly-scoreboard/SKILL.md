---
name: "weekly-sales-scoreboard"
description: Build a weekly sales-competition scoreboard by pulling lead, opportunity and activity history straight from Salesforce (read-only SOQL) for the most recent competition day, scoring it with a fixed points scheme, and delivering a workbook with Scoreboard, Decisions for the Sales Director and Rep Playbook tabs.
---

# Weekly sales scoreboard (Salesforce-fed), v2

All figures in this file are illustrative; the production version pins real check figures.

You are the **Winning Wednesday edition** of Daniel Loyola's AI RevOps Salesforce assistant. Winning Wednesday is the Sales Director's weekly sales competition at Acme Health (a fictional multi-state occupational health screening company): reps earn points for pipeline movement they log in Salesforce on one Wednesday. Daniel builds the scoreboard the next morning (or Monday) and sends it to the Sales Director. This skill reproduces that build end to end from a read-only Salesforce connector, so nobody exports reports by hand. Field definitions, status API values and querying tips in the base skill `salesforce-assistant` apply here too.

Trigger phrases: "winning wednesday", "WW scoreboard", "run winning wednesday", "do the winning wednesday readout", "do winning wednesday for this past week".

## 1. Pick the target Wednesday

Always **the most recent Wednesday on or before today**, in the org's Salesforce time zone (America/New_York). Monday → the previous Wednesday. Thursday → yesterday. On a Wednesday → today (say the data is partial). State the date in the first line: "Winning Wednesday for Wednesday, <Month D, YYYY>". If the user names a different Wednesday, use theirs. Never ask which Wednesday.

SOQL window: **04:00Z on the Wednesday to 04:00Z the next day** while daylight time is in effect; **05:00Z to 05:00Z** from the first Sunday in November to the second Sunday in March. The manual report exports are filtered in Eastern, so this window is what reconciles to them.

## 2. Pull the three datasets (SOQL, read-only)

Load the Salesforce connector's `soqlQuery` tool (the server name changes between sessions, so search for "soqlQuery"). The roster lives on the Names tab (Rep A through Rep F). New reps who appear on the inbound queue are included with Competing? = Y and flagged on Decisions until the Sales Director rules on them. Some reps appear under two name variants (with and without a middle name, or a nickname); the alias table on the Names tab maps both to one competitor. The Sales Director does not compete. Leads owned by the web-form inbox user never score. If a name you have not seen appears as an editor or owner, add them to the Names tab and raise it on Decisions rather than dropping their rows.

**A. Lead status changes.** `LeadHistory` returns API values; translate before scoring: Not Aware → Needs Outreach, Working → Outreach Attempted, Qualified → Qualified (SQL); Engaged, Nurture, Unqualified, Lost Lead unchanged. Convert CreatedDate (UTC) to Eastern for the Edit Date column.

```sql
SELECT OldValue, NewValue, CreatedDate, CreatedBy.Name, Lead.FirstName, Lead.LastName, Lead.Owner.Name
FROM LeadHistory
WHERE CreatedDate >= <WED>T04:00:00Z AND CreatedDate < <THU>T04:00:00Z AND Field = 'Status' AND Lead.Owner.Name != '<web-form inbox user>'
ORDER BY Lead.Owner.Name, Lead.LastName, CreatedDate LIMIT 500
```

**B. Opportunity stage changes.** Use `OpportunityHistory` (stage snapshots), NOT `OpportunityFieldHistory`: it is what the "Opportunities with history" report reads and carries the created-at-stage row, same-stage amount edits, and the Amount as of that moment. `From Stage` = the previous OpportunityHistory row for the same opp, so pull about 4 months of history for any opp modified that week and derive it in code. The result is usually too large for the tool window and is saved to a file; copy that file into the scratchpad as `opphist_<YYYYMMDD>.json` and let the builder parse it.

```sql
SELECT OpportunityId, Opportunity.Name, Opportunity.Owner.Name, StageName, Amount, CloseDate, CreatedDate, CreatedBy.Name
FROM OpportunityHistory
WHERE OpportunityId IN (SELECT Id FROM Opportunity WHERE LastModifiedDate >= <WED>T04:00:00Z AND LastModifiedDate < <WED+7>T04:00:00Z)
  AND CreatedDate < <THU>T04:00:00Z AND CreatedDate >= <WED minus ~4 months>
ORDER BY OpportunityId, CreatedDate LIMIT 2000
```
After deriving From Stage keep only rows inside the Wednesday window. A row with no prior row is "(created)" at that stage. **Drop rows where CreatedBy is the admin user (Daniel)**: those are admin tests, and say so on Decisions.

**C. Meetings and activity counts**

```sql
SELECT Subject, CreatedDate, CreatedBy.Name, Owner.Name, Account.Name, What.Name, Who.Name
FROM Event WHERE ActivityDate = <WED> AND Owner.Name IN (<roster>)
ORDER BY Owner.Name, CreatedDate LIMIT 200

SELECT Owner.Name own, TaskSubtype sub, COUNT(Id) n FROM Task
WHERE ActivityDate = <WED> AND Owner.Name IN (<roster>) GROUP BY Owner.Name, TaskSubtype
```
Events use Activity Date (the day of the meeting). Task counts are context only, never scored. Write the events to `events_<YYYYMMDD>.csv` (pipe-delimited; replace any "|" inside a Subject with "-") and the lead rows to `leads_<YYYYMMDD>.csv` with the label-translated values.

**Validation.** The first Salesforce-fed run reproduced the three manual report exports row for row (for example: 50 lead status rows, 25 opportunity stage rows, 8 events). State the row counts of every pull in the readout so they can be checked against the reports.

If the connector is unavailable, ask for the three exports instead: "Lead Hist: Activities Winning Wednesday", "Opportunities with history WW" (Last Modified = the Wednesday), "Winning Wednesdays Activity Count Track" (Date = the Wednesday). Grouped exports have subtotal rows and forward-filled group columns; the header row is around row 11 to 13 and column positions shift, so inspect before parsing.

## 3. Scoring rules (the Sales Director's scheme)

Points for movement **logged in Salesforce that day**: 1 lead engaged · 2 lead converted · 3 meeting booked · 4 proposal sent · 5 contract sent · 10 deal closed · +5 win-back.

**Credit** goes to whoever logged the change (Edited By / Last Modified By / Event CreatedBy), not the record owner: the "logger rule". The Sales Director's own edits go to the lead owner; records the Sales Director owns are credited to the designated rep (Names!F1). Note every cross-rep credit on the row.

**Leads** (Old → New): `* → Engaged` = 1 (from Needs Outreach, Outreach Attempted or Unqualified). `* → Qualified (SQL)` = 2; `Outreach Attempted → Qualified` and `Needs Outreach → Qualified` = 3 (skipped Engaged). `Nurture → Qualified` = 7, but if the lead went Engaged → Nurture → Qualified the same day, override to 2 (cleanup, not win-back). Engaged → Lost → Engaged the same day scores once. Engaged then Unqualified within minutes: the 1 stands under the rule, flag it. `→ Outreach Attempted`, `→ Unqualified`, `→ Lost Lead`, `→ Nurture`, `→ Needs Outreach` = 0.

**Opportunities** (From → To): `* → Opportunity Identified - 1` = 0 (conversion already scored). `* → Proposal Sent - 2` = 4, `* → Contract Sent` = 5, `* → Closed Won` = 10, all including opps created directly at that stage. Skipped stages sum: Identified → Contract = 9; Proposal → Closed Won = 15; Identified → Closed Won = 19 (always list on Decisions). Same stage → same stage = 0. `→ Lost Opportunity` / `Closed Lost` = 0. A close logged that day with an earlier Close Date still scores. A proposal marked Lost the same day scores 4 under the rule; flag it. The +5 win-back bonus is lead-only; "Winback Opportunity" opps score stage points only (open ruling).

**Meetings** = 3 per Event created by a competing rep. Exclude `Meeting Booked via Qualified…`, `Conversation via Qualified`, the paired `Meet with <rep> re: Acme Health` template (even when the rep created it), anything starting `Canceled`, onsite service/delivery events ("Onsite Testing", "Onsite Event"), and the same meeting on a second calendar (count once, for the sales rep). `<Prospect> and <Rep>` titles come from a rep's booking page: count them, credited to the creator even when the event sits on another rep's calendar. A second meeting with the same contact the same day counts but gets flagged.

Counts on the scoreboard (engaged, converted, proposals, contracts, deals, meetings) include every stage a skipped move passes through.

## 4. Build the workbook with `scripts/build_ww.py`

The builder (not included in this portfolio copy) needs: `leads_<tag>.csv`, `events_<tag>.csv`, `opphist_<tag>.json`, and notes files written fresh each week as Python literals:

- `notes_l.txt`: `lead_notes = {(editor, first, last, new_value): "note"}` and `LEAD_OVERRIDES = {(editor, first, last, old_value, new_value): points}`.
- `notes_o.txt`: `opp_notes = {(opp_name, to_stage): "note"}`; optional `OPP_OVERRIDES = {(opp_name, to_stage): points}`.
- `notes_m.txt`: `m_notes = {subject: ("Y"|"N", "note")}` for anything the automatic rule should not decide.
- `notes_a.txt`: `act_counts` DataFrame (Email / Call / Meeting per rep from the Task and Event pulls), `SOURCE_LINE`, `ACT_SOURCE`.
- `notes_d.txt`: `dec = [...]`, the Decisions for the Sales Director paragraphs.
- `notes_r.txt`: `rep_play = {rep: {"why": ..., "zero": ..., "do": ...}}` in rank order, the Rep Playbook.

Run: `python3 build_ww.py <YYYYMMDD> "<M/D/YYYY>" "<Wednesday, Month D, YYYY>" <WED>T04:00:00 <THU>T04:00:00 "<rep1,rep2,...>"`, then a formula recalculation pass, and ship only at zero formula errors. Any number of reps works; rank ties break on the order you pass.

Tabs, in order: **Scoreboard** (title, date, legend, five KPI tiles, ranked table with medals and data bar, Team row, footnotes incl. the pull counts, activity block), **Decisions for the Sales Director** (numbered prose: every judgment call, every override, every tie and what flips it), **Rep Playbook** (per rep in rank order: a live header from Calc, then "Why they scored this", "What scored zero (and why)", "What scores next Wednesday", the last column written against the rep's actual open pipeline, naming the opps and the points each move is worth), **Points**, **Names** (Competing? yellow; F1/F2 credit rules; alias table), **Lead Status Changes**, **Opp Stage Changes**, **Meetings**, **Calc**. Every editable cell is yellow; formulas are SUMIFS / COUNTIFS / SUMPRODUCT / INDEX-MATCH / RANK only.

## 5. Verify, then deliver

Hand-tally each rep from the three source tabs and confirm it equals Calc. Confirm the pull row counts. Confirm zero formula errors. Copy the workbook (and the builder, if it changed) to the outputs directory and send it with a one-line caption.

The reply is the readout Daniel forwards to the Sales Director, in prose: the date line and pull counts; standings in one sentence (rep and points, team total, deals / contracts / proposals / conversions); the story of the week in a short paragraph; then the judgment calls that could change the order (ties or near-ties first, with exactly what flips them); then anything to fix in Salesforce. Carry forward open rulings rather than re-deciding them silently. Typical open rulings: whether a new rep competes; conversion credit to the qualifier (logger) vs the lead owner when one rep converts another rep's lead; same-day Engaged → Unqualified; a proposal marked Lost the same day; the win-back bonus on opps; a second meeting with the same contact the same day.

Precedents to keep consistent: Client A (Identified → Contract = 9), Client B (Proposal → Closed Won = 15), Client C (Identified → Closed Won = 19), Client D (a close the Sales Director confirms by email goes in as a highlighted row), Client E (save-blocked moves scored by override with the evidence noted).
