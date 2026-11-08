# Data-quality flags (build_dq.py)

Lead flags (evaluated on each lead dataset)

| Code | Flag | Why it matters |
|---|---|---|
| L01 | Unqualified MQL with blank Unqualified Reason | Breaks the unqualified-reason table and Net MQL bridge |
| L02 | Lost Lead MQL with blank Lost Lead Reason | Breaks the lost-reason table |
| L03 | MQL with blank Lead Source | Attribution gap |
| L04 | MQL with Lead Category UNKNOWN or blank | Lands in Unknown bucket |
| L05 | Legacy screening-size picklist value (1-10, 1-24, 100-499, 500-999, 1000+) | Needs mapping to current buckets |
| L06 | MQL flagged Personal Email Likely | Likely individual |
| L07 | MQL whose Company reads as an individual (PPL / Self / N/A / blank) | Should be unqualified as PPL or Individual Appointment |
| L08 | Converted MQL with no Converted Opportunity | Counts as conversion, adds $0 pipeline |
| L09 | Converted lead that is NOT an MQL | In opportunity totals, not in MQL funnel |
| L10 | Converted MQL with SQL Count = 0 | Junk unqualified reason on a converted lead |
| L11 | MQL still in Needs Outreach (Not Aware) | Never worked |
| L12 | Unqualified/Lost reason set but Status does not match | Leftover reason |
| L13 | Lead with blank Email | Cannot match to HubSpot |
| L14 | Net MQL true but Status Unqualified with a removal reason | Formula and reason disagree |

Opportunity flags

| Code | Flag |
|---|---|
| O01 | Blank Lead Category |
| O02 | Lead Category case/label variant (Organic, Other) |
| O03 | Blank, zero or $1 Amount |
| O04 | Closed Won with blank New Close Date |
| O05 | Closed Won with future New Close Date |
| O06 | Closed Won where Close Date month differs from New Close Date month |
| O07 | Closed Lost / Lost Opportunity with blank New Close Date |
| O08 | Blank Lead Source |
| O09 | Open opportunity with Close Date in the past |
| O10 | Lost Opportunity with blank Lost Opportunity Reason |
| O11 | Blank Type (Revenue Type is blank org-wide, noted on the Summary tab, not flagged per record) |
| O12 | Blank Account |
| O13 | Is MQL? false but inbound Lead Source (Lead Gen Form / Qualified.com / Inbound Phone Call) |
| O14 | New Close Date earlier than Created Date (backdated close) |
