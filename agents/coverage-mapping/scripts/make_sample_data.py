#!/usr/bin/env python3
"""
Generate FAKE sample data for the coverage-mapping demo.

Everything this script writes is synthetic: site names, addresses, ZIP codes,
cities, and coordinates are invented. Nothing comes from a real provider network
or client. Output goes to ../sample-data/:

  zip_centroids_sample.csv   zip, lat, lon, city, state   (small fake ZIP table)
  network_sites.csv          in-house network (NOL) sites
  partner_a_sites.csv        Partner Network A clinics (occ health, no blood/urine)
  partner_b_sites.csv        Partner Network B lab sites (blood draw & urine only)
  client_locations.csv       a fake client's location list, including messy ZIPs
                             that exercise the ZIP-repair rules

Usage:  python scripts/make_sample_data.py
"""
import csv, os, random

random.seed(42)
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "sample-data")
os.makedirs(OUT, exist_ok=True)

# Fake metro clusters: (state, ZIP prefix, center lat, center lon, fake city names)
CLUSTERS = [
    ("CT", "064", 41.30, -72.90, ["Harborview", "Elm Point", "Stonebridge"]),
    ("NJ", "079", 40.80, -74.40, ["Maple Glen", "Kingsford", "Ridgemont"]),
    ("TX", "750", 32.80, -96.80, ["Cedar Falls", "Lone Oak", "Prairie Bend"]),
    ("IL", "606", 41.88, -87.63, ["Lakeshore", "North Haven", "Westbrook"]),
    ("AZ", "850", 33.45, -112.07, ["Desert Vista", "Sun Ridge", "Canyon Park"]),
    ("MT", "596", 46.60, -112.00, ["Pine Hollow", "Bitterroot", "Big Sky Flats"]),  # no providers: gap area
]

def jitter(lat, lon, miles):
    # ~69 miles per degree of latitude; good enough for fake data
    return (round(lat + random.uniform(-miles, miles) / 69.0, 4),
            round(lon + random.uniform(-miles, miles) / 52.0, 4))

zips = []  # (zip, lat, lon, city, state)
for st, pre, la, lo, cities in CLUSTERS:
    for i in range(1, 16):
        lat, lon = jitter(la, lo, 10)
        zips.append((f"{pre}{i:02d}", lat, lon, cities[i % len(cities)], st))

with open(os.path.join(OUT, "zip_centroids_sample.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["zip", "lat", "lon", "city", "state"]); w.writerows(zips)

by_state = {}
for z in zips:
    by_state.setdefault(z[4], []).append(z)

streets = ["Main St", "Oak Ave", "Commerce Dr", "Industrial Pkwy", "Market St", "Park Blvd", "Center Rd"]
def addr():
    return f"{random.randint(100, 9999)} {random.choice(streets)}"

# Coverage design so the demo shows every class:
#   CT, NJ, IL -> network (NOL) sites           => Full NOL Coverage
#   TX         -> Partner A + Partner B only     => Partner A + Partner B
#   AZ         -> Partner B only                 => Partner B Only
#   MT         -> nothing                        => No Coverage (closest shown, flagged)
nol_states = {"CT": 3, "NJ": 3, "IL": 2}
pa_states = {"CT": 2, "NJ": 1, "TX": 3, "IL": 2}
pb_states = {"CT": 2, "NJ": 2, "TX": 3, "IL": 3, "AZ": 3}

with open(os.path.join(OUT, "network_sites.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["LocationName", "Address1", "CityName", "StateName", "Zip"])
    n = 1
    for st, k in nol_states.items():
        for z in random.sample(by_state[st], k):
            w.writerow([f"Acme Network Clinic {n:03d}", addr(), z[3], st, z[0]]); n += 1

with open(os.path.join(OUT, "partner_a_sites.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["Name", "Address", "City", "State", "Zip"])
    n = 1
    for st, k in pa_states.items():
        for z in random.sample(by_state[st], k):
            w.writerow([f"Partner A Clinic {n:03d}", addr(), z[3], st, z[0]]); n += 1

with open(os.path.join(OUT, "partner_b_sites.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["Name", "Address1", "City", "State", "Zip"])
    for st, k in pb_states.items():
        for z in random.sample(by_state[st], k):
            w.writerow(["PARTNER B", addr(), z[3], st, z[0]])

# Fake client location list, including messy inputs that exercise ZIP repair
rows, n = [], 1
for st, *_ in CLUSTERS:
    for z in random.sample(by_state[st], 3):
        rows.append([f"Client A Site {n:02d}", z[3], st, z[0]]); n += 1
ct = by_state["CT"]
rows += [
    [f"Client A Site {n:02d}",   ct[0][3], "CT", ct[0][0] + "-1234"],        # ZIP+4 with dash
    [f"Client A Site {n+1:02d}", ct[1][3], "CT", ct[1][0].lstrip("0")],      # leading zero lost (4 digits)
    [f"Client A Site {n+2:02d}", "",       "CT", ct[2][0][1:] + "1234"],     # 8-digit ZIP+4 that lost its leading 0
    [f"Client A Site {n+3:02d}", "",       "NJ", "07999"],                   # not in ZIP DB -> nearest valid in state
    [f"Client A Site {n+4:02d}", by_state["TX"][0][3], "TX", ""],            # no ZIP: City + State only
]
with open(os.path.join(OUT, "client_locations.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["Location Name", "City", "State", "Postal Code"]); w.writerows(rows)

print(f"Wrote fake sample data to {OUT}")
for fn in sorted(os.listdir(OUT)):
    print("  ", fn)
