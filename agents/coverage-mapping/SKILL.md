---
name: coverage-mapping
description: Build an Acme Health medical-testing COVERAGE MAP / gap analysis workbook for a client location list. Use when a user uploads a list of client sites, ZIP codes, cities, or a "Mapping Request for [client name]" file and asks for coverage mapping, a coverage report, a gap analysis, provider proximity, or which locations are near the in-house network (NOL), Partner Network A, or Partner Network B. Produces the standard 12-tab Excel coverage report (Coverage Summary, NOL / Partner A / Partner B mapping within 25 miles, interactive ZIP Lookup, full provider lists).
---

# Coverage Mapping (NOL · Partner Network A · Partner Network B)

> Portfolio version by Daniel Loyola. Company, client, and partner details are anonymized; the demo runs on synthetic data.

The deliverable is **one Excel workbook**: `<Client>_Coverage Report <date>.xlsx`, identical in
format to the coverage reports delivered to enterprise clients. It is NOT a city-to-ZIP lookup or a
merged list. Everything is produced by the bundled script: do not re-implement the logic.

## What the script does
For every client location it geocodes the ZIP (offline ZIP centroid table), finds every
provider within **25 miles** (default; `--radius` to change) and classifies worst-first:

| Class | Meaning |
|---|---|
| 🔴 No Coverage Within 25mi | no NOL, Partner A, or Partner B site in range |
| 🟠 Partner B Only | blood draw & urine collection only |
| 🟡 Partner A Only / Partner A + Partner B | all occ-health EXCEPT blood/urine (no full-service NOL) |
| 🟢 Full NOL Coverage | in-house network site in range (physicals, drug screens, urine, TB) |

If a provider type has nothing in range, the single **closest** one is shown, flagged ⚠️.
Provider files are found automatically in `--providers-dir` (default `sample-data/`).

## Input the user gives you
Any xlsx/csv. Columns are auto-detected (case-insensitive), any of:
- ZIP only · State + ZIP ("Address Book State", "Postal Code") · Name + City + State + ZIP
- City + State with no ZIP (geocoded from city/state)
Multi-sheet workbooks: the first sheet with a ZIP-like column is used (`--sheet` to override).

ZIP hygiene is automatic and recorded in the **Geo Note** column: ZIP+4 trimmed, leading zeros
restored, 8-digit "ZIP+4 that lost its leading 0" repaired (e.g. 64031234 to 06403), ZIPs missing
from the database mapped to the nearest valid in-state ZIP. The original value stays visible.

## Steps
1. **Get the client name.** It is usually in the filename or request ("Mapping Request for Client A").
   If it is genuinely absent, ask: it drives the titles and output filename. Do not guess.
2. **Run the script:**
   ```bash
   python scripts/build_coverage.py \
     --input "<client file>" \
     --client "<Client Name>" \
     --providers-dir <folder with the 3 provider files> \
     --zip-db <zip centroid csv> \
     --out <output folder>
   ```
   Options: `--radius 30` · `--sheet "Sheet2"` · `--date 10.21.2026`
   Requires pandas + openpyxl only (no network, no other packages).
3. **Read the console output.** It prints the detected columns, location count, number of
   ZIPs corrected, and the coverage breakdown. If column detection picked the wrong field,
   re-run with a cleaned copy of the input or tell the user what to rename.
4. **Report back** (short, decision-ready):
   - the coverage breakdown as a small table (counts per class, total locations)
   - where the 🔴/🟠 gaps cluster (by state, computed from the Coverage Summary tab)
   - every ZIP that was corrected or flagged, with what was done (from Geo Note)
   - anything unmapped ("ZIP not found" rows) that the user must verify
   - link to the workbook
5. Never deliver only a ZIP list or a partial workbook. If the script errors, fix the input
   (not the classification logic) and re-run.

## Files in this skill
- `scripts/build_coverage.py`: the builder (CLI; self-contained)
- `scripts/make_sample_data.py`: generates the synthetic demo data
- `sample-data/`: fake provider files, fake ZIP table, fake client list
- `sample-output/`: the workbook produced from the sample data
- `reference/methodology.md`: classification rules, service definitions, ZIP-repair rules
