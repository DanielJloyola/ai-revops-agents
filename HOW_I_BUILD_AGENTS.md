# How I Build Agents

The method behind every agent in this repo.

## 1. Start from a real, recurring job

I only build an agent for work that repeats and has a clear owner: a weekly report, a question leadership asks every Monday, a deliverable sales needs for every enterprise prospect. If I cannot name who uses the output and how often, I do not build it.

## 2. Decide where AI belongs, and where it does not

Most of a reporting workflow is deterministic. Pulling records, counting them, and joining them should be code or SOQL, not a model. I use the model for the parts that need judgment or language: mapping a plain-English question to the right definition, choosing the right pipeline scope, explaining a variance, and drafting the narrative. If a Flow, a formula field, or a Python script does the job reliably, that is the answer.

## 3. Encode the business definitions first

Before any prompt, I write down how the business actually counts: what an MQL is, which unqualified reasons remove a lead from Net MQL, which date field defines revenue, which picklist label maps to which API value. These rules go into the skill as non-negotiable instructions. Most wrong answers come from a model using a reasonable definition instead of the org's definition.

## 4. Document the traps

Every org has fields that look right and are wrong: a checkbox that is true on records it should not be, a standard date that is not maintained, a relationship that silently drops rows. I record each trap in the skill with the correct pattern, so the agent avoids it every time.

## 5. Build the validation before trusting the output

- Reconcile row for row against the production report export on the first runs.
- Enforce row counts against a SOQL count query on every extract.
- Pin check figures from standing reports so drift shows up immediately.
- Abort on mismatch. A stopped run is a five-minute fix; a wrong number in a Board deck is a credibility problem.

## 6. Keep access read-only and governed

Agents read through a dedicated read-only connection (MCP server with an API-only integration user and JWT auth). Writes to the CRM stay with people and change-managed Flows.

## 7. Keep a human gate where the stakes are high

Board and executive reporting runs in two phases: the agent builds a draft and stops; I proof it; then the final phase applies my decisions and runs the tie-outs.

## 8. Ship small, then extend

Version 1 of the weekly scoreboard ran on manual report exports. Version 2 pulls from Salesforce directly, and only shipped after it reproduced the manual exports row for row.
