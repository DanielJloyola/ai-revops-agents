# Coverage Mapping: Methodology

## Provider types and what they can do
| Provider | Services | Source file |
|---|---|---|
| **NOL** (in-house network) | FULL occupational health: physicals, drug screens, urine collection, TB tests | `network_sites.csv` (active, full-service sites only; see "Building the NOL list" below) |
| **Partner Network A** | All occupational health EXCEPT blood draw & urine collection | `partner_a_sites.csv` |
| **Partner Network B** | Blood draw & urine collection ONLY | `partner_b_sites.csv` |

## Distance
Great-circle (haversine) distance between ZIP centroids, in statute miles. Default radius
**25 miles**. Centroids come from an offline ZIP centroid CSV (`zip, lat, lon, city, state`).

## Classification (evaluated in this order, worst first in the report)
1. **Full NOL Coverage**: at least one NOL site within radius (regardless of others) = 🟢 Covered
2. **Partner A + Partner B**: no NOL, but both partner types in range = 🟡 Low priority (partial)
3. **Partner A Only**: no NOL, no Partner B = 🟡 Low priority (partial)
4. **Partner B Only**: only blood/urine available = 🟠 Medium priority
5. **No Coverage Within radius**: nothing in range = 🔴 High priority (recruit a provider)

For each location the report also shows the **count** of each provider type in range and the
**closest** of each type with its distance. If a type has none in range the closest one is still
listed, flagged "⚠️ OUTSIDE 25mi (closest)" and shaded orange.

## Location universe rules
- One row per distinct (name, city, state, ZIP). Exact duplicates are dropped.
- City is derived from the ZIP when the input has none; state is derived if missing.
- A location with no ZIP but City + State is geocoded from the city (Geo Note says so).

## ZIP repair rules (all recorded in the Geo Note column; original value kept for display)
| Input looks like | Action |
|---|---|
| `06902-1234`, `069021234` (9 digits) | use first 5: `06902` |
| `6902` (4 digits, leading 0 lost by Excel) | zero-pad: `06902` |
| `79222116` (8 digits = ZIP+4 that lost its leading 0) | `0` + first 4: `07922` |
| valid-looking but absent from the ZIP DB | nearest valid ZIP in the same state with the same first 3 digits |
| blank / unparseable | geocode via City + State; else "ZIP not found" = ⚠️ Verify location |

## Building the NOL list (upstream filter)
The in-house network list is derived from a weekly branch report with three filters, in order:
1. **Branch type:** keep only in-house and contracted full-service branch types. Partner networks are
   excluded here because they are mapped separately as Partner A / Partner B.
2. **Active status:** keep only active branches.
3. **Limited-service exclusion:** drop any site whose name contains the word "only" (X-ray Only,
   Drug Screen Only, Exams Only, etc.), or a standalone limited-service marker such as XRAY / X-RAY,
   RFT, or AUDIOGRAM as a **whole word**. Whole-word matching matters: it catches "Woodbridge XRAY"
   while keeping place names like Patriot, Patterson, or Patchogue.

## Workbook tabs
Coverage Summary · NOL Mapping · Partner A Mapping · Partner B Mapping · ZIP Lookup (type any ZIP to
see the closest 10 of each type, live formulas) · NOL / Partner A / Partner B Full List · 4 hidden
helper sheets (`_ZIP_C`, `_NOL_D`, `_PA_D`, `_PB_D`) that power the ZIP Lookup. ZIPs are stored as text.
