# Coverage Mapping Agent

Turns a client's list of work sites into a decision-ready coverage gap report: for every site, which testing providers are within 25 miles, what services that covers, and where the gaps are.

## Problem
Enterprise clients send location lists (often messy: ZIP+4, lost leading zeros, missing ZIPs) and ask "can you cover all of these?" Answering by hand meant hours of lookups across three provider networks with different service capabilities.

## How it works
- Geocodes every client location from an offline ZIP centroid table (no API calls).
- Computes **Haversine** great-circle distance to every site in three networks: the in-house network (full service), Partner Network A (all occupational health except blood/urine), and Partner Network B (blood draw and urine only).
- Classifies each location worst-first: No Coverage, Partner B Only, Partner A (+B), Full Coverage, and flags the closest provider when nothing is in range.
- Writes a 12-tab Excel workbook: Coverage Summary, three mapping tabs, an interactive ZIP Lookup (live Excel formulas, type any ZIP), full provider lists, and hidden helper sheets.
- Runs as a Claude skill: the agent gets the client name, runs the script, and reports the breakdown, gap clusters, and every corrected ZIP.

## Guardrails
- ZIP repair rules are deterministic and every fix is written to a Geo Note column, with the original value kept.
- Unresolvable locations are flagged "Verify location" instead of silently dropped.
- The agent is instructed to fix the input, never the classification logic, and never to deliver a partial workbook.

## Result
Used in production for enterprise client coverage mapping; delivered for three enterprise clients. The production version covers hundreds of network sites and ~42,000 US ZIPs.

## Run the demo
```bash
pip install pandas openpyxl
python scripts/make_sample_data.py
python scripts/build_coverage.py --input sample-data/client_locations.csv \
  --client "Client A" --providers-dir sample-data \
  --zip-db sample-data/zip_centroids_sample.csv --out sample-output
```
A pre-built example is in `sample-output/`.

## Data note
All data here is synthetic (fake sites, ZIPs, cities, and coordinates). Real provider and client data is not included. For real use, supply your own provider files and a public ZIP centroid file, for example the U.S. Census ZCTA Gazetteer (columns: zip, lat, lon, city, state).
