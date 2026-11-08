# Paid Ads Assistant

A Claude skill that traces Google Ads campaigns through the full Salesforce funnel (lead, MQL, Net MQL, conversion, pipeline, Closed Won) using read-only SOQL, and catches the attribution errors that make paid reporting unreliable.

## Problem

"What did our ads actually produce?" is hard to answer from Salesforce. UTM tags are messy, the same campaign shows up under several mediums, keywords land in the wrong fields, and the Lead Category formula misfiles some paid leads as DIRECT or ORGANIC. A simple PAID filter undercounts and misattributes.

## How it works

- A campaign map normalizes raw `UTM_Campaign__c` values into reportable campaign names and flags anything unmapped.
- Standard rollup queries return volume, funnel, and pipeline per campaign in one pass.
- A two-pass lookup for any specific campaign or tracking URL: first inside PAID for the period, then across every category and every attribution field (main, first-touch, last-touch, legacy, Pardot, HubSpot drilldowns).
- A display and video sweep checks every Medium field plus the paid sub-type formula, so retargeting and video leads are never missed.
- Cost per lead, MQL, Net MQL, and conversion are computed only when the asker supplies Google Ads spend.

## Guardrails

- **Never estimates spend, clicks, or impressions:** those are not in Salesforce.
- **Shares funnel definitions** with the Salesforce RevOps Assistant, which is the source of truth if they ever disagree.
- **Calls out misfiled leads and spam** instead of counting them as wins.
- **Reconciles conversions against opportunities** and labels cohort Closed Won separately from Closed Won by close date.
- **States the filters used** so every number can be rebuilt in a Salesforce report.

## Result

- Answers paid attribution questions in plain language, from campaign to Closed Won.
- Reconciles to production dashboard numbers.

Shown with illustrative data; company details removed.
