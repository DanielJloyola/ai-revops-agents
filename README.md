# AI RevOps Agents

Production AI agents I built and run as the sole Revenue Operations owner at a multi-state occupational health screening company. They sit on top of Salesforce and HubSpot, read live CRM data through a read-only Salesforce MCP server and SOQL, and produce the pipeline answers, rep scorecards, coverage reports, and weekly C-suite and Board reporting the business runs on.

> Shown here with illustrative and synthetic data. The company is renamed "Acme Health"; client, colleague, and financial details are removed.

**Author:** Daniel Jay Loyola, Revenue Operations Lead & CRM Architect · [LinkedIn](https://www.linkedin.com/in/daniel-jay-loyola)

## The problem

One person owns RevOps for Sales, Marketing, Customer Success, Account Management, and a network-partner team, plus weekly reporting to the CFO, CEO, CRO, and Board. Questions, reports, and client deliverables arrive faster than one person can build them by hand, and every number has to match what leadership sees in Salesforce.

## What I built

Agents and skills built with Claude and Claude Code. Each one encodes the org's business definitions (MQL, Net MQL, the revenue close-date rule, pipeline scopes) so the model answers the way the business counts, then uses tools over live CRM data.

| Agent | What it does | Highlights |
|---|---|---|
| [salesforce-assistant](agents/salesforce-assistant) | Answers lead, pipeline, and revenue questions in plain language | Org definitions as rules, three named pipeline scopes, known data traps documented |
| [paid-ads-assistant](agents/paid-ads-assistant) | Traces Google Ads campaigns through the full funnel to Closed Won | Catches attribution errors that make paid reporting unreliable |
| [weekly-scoreboard](agents/weekly-scoreboard) | Scores every rep weekly from Salesforce activity, leads, and stage changes | First Salesforce-fed run reproduced three manual exports row for row |
| [salesforce-weekly-pull](agents/salesforce-weekly-pull) | Pulls the weekly report extracts for the prior Monday to Sunday | Enforces row-count match against SOQL count queries |
| [weekly-reports-runner](agents/weekly-reports-runner) | Runs the weekly Red Green, Board, and Ops reporting cycle | Draft and final phases with a human proof gate and tie-out checks |
| [exec-monthly-readout](agents/exec-monthly-readout) | Builds the monthly executive data pack from live pulls | Data-quality flag workbook, month-over-month and year-over-year tables |
| [quarterly-deck](agents/quarterly-deck) | Builds the frozen data pack behind the quarterly marketing recap | Hard abort on any dataset-vs-aggregate mismatch |
| [coverage-mapping](agents/coverage-mapping) | Turns a client's site list into a 12-tab provider coverage report | Haversine proximity model; runnable demo on synthetic data |

## How the numbers stay right

An agent that is wrong with confidence is worse than no agent. Every agent here is built to prove its numbers before anyone sees them:

- **Encoded definitions.** Business rules live in the skill, not in the model's guesses (for example: revenue uses the maintained close-date field, never the standard one; query API values, not labels).
- **Row-for-row reconciliation** against production report exports.
- **Row-count checks** against SOQL count queries on every extract.
- **Pinned check figures** tied to standing Salesforce reports, so drift is caught immediately.
- **Hard abort** when a dataset and its aggregate disagree, instead of producing a plausible wrong answer.
- **Read-only, governed access.** A dedicated read-only Salesforce MCP server with an API-only integration user and JWT authentication.

## Results

- An 8+ hour weekly reporting task now runs in about 2 minutes.
- 24 automations, estimated at ~1,950 hours a year (about 1.1 FTE).
- Agents used daily by colleagues and rolling out to leadership.
- Coverage reports delivered for three enterprise clients.

## Architecture

```
Salesforce + HubSpot
        |
  read-only MCP server / SOQL
        |
  Claude skills (definitions + rules + tools)
        |
  reconciliation layer (row counts, check figures, abort on mismatch)
        |
  answers, Excel workbooks, PowerPoint slides, Board reports
```

## Repo layout

```
agents/<agent>/SKILL.md      the skill instructions Claude follows
agents/<agent>/README.md     problem, approach, guardrails, result
agents/<agent>/scripts/      Python / Node helpers (where applicable)
HOW_I_BUILD_AGENTS.md        my method for scoping, building, and validating agents
```

## Stack

Claude, Claude Code, MCP, Salesforce (Certified Administrator), SOQL, HubSpot, Python (pandas, openpyxl, python-pptx), Node (docx, pptxgenjs), Excel.
