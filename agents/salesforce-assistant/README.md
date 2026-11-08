# Salesforce RevOps Assistant

A Claude skill that answers lead, pipeline, and revenue questions in plain language by querying Salesforce (read-only SOQL), using the org's own definitions so every answer matches the production dashboards.

## Problem

Leadership and sales asked the same pipeline questions every week ("How many Net MQLs this quarter?", "What closed in Q3?"), and the honest answer depended on knowing which fields, filters, and date rules the org actually uses. Simpler queries ran fine but returned the wrong number. A sole RevOps owner could not field every question by hand.

## How it works

- Business definitions (Lead, MQL, Net MQL, SQL, three pipeline scopes, Closed Won) are encoded as a skill the agent must follow.
- The agent queries live Salesforce data through a read-only connection (MCP and SOQL); it never writes to the org.
- Label-to-API translation is built in (for example, "Needs Outreach" is stored as `Not Aware`).
- Lead pivots always carry the seven dimensions sales and marketing use to read a lead list.
- Recipes cover funnel counts, open pipeline, Closed Won by quarter and rep, and close-date reconciliation.

## Guardrails

- **Pinned check figures:** the production version carries the standing report's numbers so drift is caught immediately.
- **Known traps documented:** Net MQL must be paired with Is MQL; conversions come from the Lead side, not the opportunity semi-join; revenue uses New Close Date, not Close Date.
- **Scope labeling:** every answer names which of the three pipeline scopes it used and reconciles them when mixed.
- **Refuses what it cannot know:** realized revenue lives in the billing system, so the agent says so instead of approximating.
- **Transparent filters:** every answer states the filters applied so the asker can rebuild it in a Salesforce report.

## Result

- Answers pipeline questions in plain language, reconciled to production dashboard numbers.
- Used daily by colleagues and rolling out to leadership.

Shown with illustrative data; company details removed.
