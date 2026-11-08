# Closed-won marketing attribution

> All figures are illustrative.

Closed Won by **New Close Date** in month, any created period. Two scopes:

- **All-in**: every Closed Won with New Close Date in the month.
- **Marketing-attributed**: all-in minus deals on accounts with no marketing tie (used for ROAS, MER, CAC).

## The consistent rule ("same rule")

A deal is attributed if any of these is true:
1. the opp itself has a `Lead_Category__c`;
2. another opp on the same account has a `Lead_Category__c`;
3. a lead with a real category (not UNKNOWN) converted into the account (`Lead.ConvertedAccountId`).

UNKNOWN-only leads do not count. Parent-account rollups were tested and are not the rule.

Lookups for accounts whose won opp has no category:
```sql
SELECT AccountId, Account.Name, COUNT(Id) n FROM Opportunity WHERE Lead_Category__c != null AND AccountId IN (...) GROUP BY AccountId, Account.Name
SELECT ConvertedAccountId, Company, Lead_Category__c FROM Lead WHERE IsConverted = true AND ConvertedAccountId IN (...)
```

## Why this file exists

Published deck figures did not always follow one rule month to month (for example, a deck showed 40 | $900,000 where the same rule gives 31 | $700,000 because untied deals were kept). The agent's job is to make the rule explicit.

**Never silently change the attributed numbers.** Show deck basis and same-rule numbers side by side, put the rule switch in the workbook as an input cell, and let the user choose. Once a rule is chosen, record it here and apply it to every month.
