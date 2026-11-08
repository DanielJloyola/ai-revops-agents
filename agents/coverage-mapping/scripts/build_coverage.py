#!/usr/bin/env python3
"""
MEDICAL TESTING COVERAGE MAP: generic builder (any client)
Author: Daniel Loyola

For every client location, finds every in-house network site (NOL), Partner
Network A clinic, and Partner Network B lab site within RADIUS miles (default
25). If a provider type has NOTHING in range, the single CLOSEST one is shown
instead (flagged) so gaps are obvious.

Classification (worst first):
  No Coverage Within 25mi > Partner B Only > Partner A Only / Partner A + Partner B
  > Full NOL Coverage

Service context:
  NOL        full occupational health: physicals, drug screens, urine collection, TB tests
  Partner A  all occupational health EXCEPT blood draw & urine collection
  Partner B  blood draw & urine collection ONLY

INPUT (xlsx or csv, columns auto-detected, case-insensitive):
  ZIP only | State + ZIP | Name + City + State + ZIP | City + State (no ZIP)
  Multi-sheet workbooks: first sheet with a ZIP-like column is used (--sheet to override).

OUTPUT: <Client>_Coverage Report <date>.xlsx with 12 tabs:
  Coverage Summary | NOL / Partner A / Partner B Mapping | ZIP Lookup (interactive)
  | NOL / Partner A / Partner B Full List | 4 hidden helper sheets (_ZIP_C,_NOL_D,_PA_D,_PB_D)

PROVIDER FILES (in --providers-dir, default ../sample-data):
  network_sites.csv    LocationName, Address1, CityName, StateName, Zip
  partner_a_sites.csv  Name, Address, City, State, Zip
  partner_b_sites.csv  Name, Address1, City, State, Zip

ZIP GEOCODING: offline CSV (zip, lat, lon, city, state) passed with --zip-db.
  Default: reference/zip_centroids.csv (public ZIP centroid data, not bundled).

USAGE
  python scripts/build_coverage.py --input sample-data/client_locations.csv \
      --client "Client A" --providers-dir sample-data \
      --zip-db sample-data/zip_centroids_sample.csv --out sample-output
"""
import os, re, sys, csv, glob, argparse, datetime
import pandas as pd
from math import radians, sin, cos, sqrt, atan2
from openpyxl import Workbook, load_workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter

HERE      = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(HERE)
REF_DIR   = os.path.join(SKILL_DIR, "reference")
SAMPLE_DIR = os.path.join(SKILL_DIR, "sample-data")
ZIP_DB_PATH = os.path.join(REF_DIR, "zip_centroids.csv")   # overridden by --zip-db

RADIUS_MILES = 25
TOP_N        = 10
NOL_SVC = 'Full occupational health: physicals, drug screens, urine collection, TB tests'
PA_SVC = 'All occupational health EXCEPT blood draw & urine collection'
PB_SVC  = 'Blood draw & urine collection ONLY'

STATE_ABBR = {
 'ALABAMA':'AL','ALASKA':'AK','ARIZONA':'AZ','ARKANSAS':'AR','CALIFORNIA':'CA','COLORADO':'CO',
 'CONNECTICUT':'CT','DELAWARE':'DE','FLORIDA':'FL','GEORGIA':'GA','HAWAII':'HI','IDAHO':'ID',
 'ILLINOIS':'IL','INDIANA':'IN','IOWA':'IA','KANSAS':'KS','KENTUCKY':'KY','LOUISIANA':'LA',
 'MAINE':'ME','MARYLAND':'MD','MASSACHUSETTS':'MA','MICHIGAN':'MI','MINNESOTA':'MN',
 'MISSISSIPPI':'MS','MISSOURI':'MO','MONTANA':'MT','NEBRASKA':'NE','NEVADA':'NV',
 'NEW HAMPSHIRE':'NH','NEW JERSEY':'NJ','NEW MEXICO':'NM','NEW YORK':'NY','NORTH CAROLINA':'NC',
 'NORTH DAKOTA':'ND','OHIO':'OH','OKLAHOMA':'OK','OREGON':'OR','PENNSYLVANIA':'PA',
 'RHODE ISLAND':'RI','SOUTH CAROLINA':'SC','SOUTH DAKOTA':'SD','TENNESSEE':'TN','TEXAS':'TX',
 'UTAH':'UT','VERMONT':'VT','VIRGINIA':'VA','WASHINGTON':'WA','WEST VIRGINIA':'WV',
 'WISCONSIN':'WI','WYOMING':'WY','DISTRICT OF COLUMBIA':'DC'}
STATES = set(STATE_ABBR.values())

def norm_state(v):
    s = str(v).replace('\xa0', ' ').strip().upper()
    if s in ('', 'NAN', 'NONE'): return ''
    if s in STATE_ABBR: return STATE_ABBR[s]
    return s[:2] if len(s) >= 2 else s

# ── GEO ─────────────────────────────────────────────────────────────────────
def haversine(lat1, lon1, lat2, lon2):
    R = 3958.8
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    a = sin((lat2-lat1)/2)**2 + cos(lat1)*cos(lat2)*sin((lon2-lon1)/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1-a))

def clean_zip(z):
    if z is None: return ''
    s = re.sub(r'[^0-9]', '', str(z).split('-')[0].split('.')[0])
    return s.zfill(5) if s else ''

# ZIP database: bundled CSV first, `zipcodes` package as fallback
_ZDB = {}          # zip -> (lat, lon, city, state)
_BY_STATE = {}     # state -> [zip, ...]
_BY_CITY = {}      # (CITY, ST) -> zip
def _load_zdb():
    if _ZDB: return
    p = ZIP_DB_PATH
    if os.path.exists(p):
        with open(p, newline='', encoding='utf-8') as f:
            for r in csv.DictReader(f):
                try: lat, lon = float(r['lat']), float(r['lon'])
                except Exception: continue
                _ZDB[r['zip']] = (lat, lon, r['city'], r['state'])
    else:
        try:
            import zipcodes as zc
            for z in zc.list_all():
                if z.get('lat') and z.get('long'):
                    _ZDB[z['zip_code']] = (float(z['lat']), float(z['long']), z['city'], z['state'])
        except ImportError:
            sys.exit(f"ERROR: ZIP database {ZIP_DB_PATH} missing and `zipcodes` package not installed. Pass --zip-db.")
    for z, (la, lo, c, st) in _ZDB.items():
        _BY_STATE.setdefault(st, []).append(z)
        _BY_CITY.setdefault((c.upper(), st), z)
    print(f"  ZIP database: {len(_ZDB):,} ZIPs")

def get_coords(z):
    z = clean_zip(z); r = _ZDB.get(z)
    return (r[0], r[1]) if r else None

def city_from_zip(z):
    r = _ZDB.get(clean_zip(z)); return r[2] if r else ''

def get_coords_city(city, state):
    city = str(city).replace('\xa0', ' ').strip().upper(); st = norm_state(state)
    if not city or len(st) != 2: return None
    z = _BY_CITY.get((city, st))
    return get_coords(z) if z else None

def nearest_valid_zip(z, state):
    """ZIP absent from DB: numerically-closest valid ZIP in the same state sharing
    the first 3 digits (same sectional center): a close geographic proxy."""
    cands = [c for c in _BY_STATE.get(state, []) if c[:3] == z[:3]]
    if not cands:  # no state given / no match: any ZIP with same first 3 digits
        cands = [c for c in _ZDB if c[:3] == z[:3]]
    return min(cands, key=lambda c: abs(int(c) - int(z))) if cands else None

def repair_zip(raw, state):
    """Return (zip_for_geo, display_zip, note). Handles ZIP+4, dropped leading zeros,
    8-digit 'ZIP+4 with leading 0 lost', and ZIPs missing from the DB."""
    s = re.sub(r'[^0-9]', '', str(raw).split('.')[0])
    if not s: return None, str(raw), 'blank/invalid ZIP'
    if len(s) == 9:                       # ZIP+4 run together
        s = s[:5]
    elif len(s) == 8:                     # ZIP+4 that lost a leading 0
        s = '0' + s[:4]
        note = f'malformed ZIP {raw} read as ZIP+4 with leading 0 dropped -> {s}'
        return (s if get_coords(s) else None), str(raw), note
    elif len(s) > 9:
        return None, str(raw), f'unrecognised ZIP {raw}'
    z = s.zfill(5)
    if get_coords(z): return z, z, ''
    nz = nearest_valid_zip(z, state)
    if nz: return nz, z, f'ZIP {z} not in ZIP DB -> geo via nearest valid {nz} ({city_from_zip(nz)})'
    return None, z, f'ZIP {z} not in ZIP DB (could not resolve)'

# ── INPUT DETECTION ─────────────────────────────────────────────────────────
ZIP_PAT   = re.compile(r'zip|postal', re.I)
STATE_PAT = re.compile(r'^state$|\bstate\b|^st$|province', re.I)
CITY_PAT  = re.compile(r'^city$|\bcity\b|town', re.I)
NAME_PAT  = re.compile(r'name|location|community|facility|site|branch|account|office|store|center', re.I)

def _pick(cols, pat, exclude=()):
    for c in cols:
        if c in exclude: continue
        if pat.search(str(c)): return c
    return None

def read_input(path, sheet=None):
    ext = os.path.splitext(path)[1].lower()
    if ext in ('.xlsx', '.xlsm', '.xls'):
        xl = pd.ExcelFile(path)
        sheets = [sheet] if sheet else xl.sheet_names
        for sh in sheets:
            df = pd.read_excel(path, sheet_name=sh, dtype=str)
            df.columns = [str(c).strip() for c in df.columns]
            if _pick(df.columns, ZIP_PAT) or (_pick(df.columns, CITY_PAT) and _pick(df.columns, STATE_PAT)):
                print(f"  Input sheet: '{sh}'"); return df
        # header not on row 1? try to find it
        for sh in sheets:
            raw = pd.read_excel(path, sheet_name=sh, header=None, dtype=str)
            for i in range(min(15, len(raw))):
                hdr = [str(x).strip() for x in raw.iloc[i].tolist()]
                if any(ZIP_PAT.search(h) for h in hdr):
                    df = raw.iloc[i+1:].copy(); df.columns = hdr
                    print(f"  Input sheet: '{sh}' (header on row {i+1})"); return df
        sys.exit("ERROR: no sheet with a ZIP/Postal (or City+State) column found. Use --sheet.")
    df = pd.read_csv(path, dtype=str, encoding='utf-8', encoding_errors='replace')
    df.columns = [str(c).strip() for c in df.columns]
    return df

def load_footprint(path, sheet=None):
    df = read_input(path, sheet)
    cols = list(df.columns)
    zc = _pick(cols, ZIP_PAT); sc = _pick(cols, STATE_PAT); cc = _pick(cols, CITY_PAT)
    nc = _pick(cols, NAME_PAT, exclude=(zc, sc, cc))
    print(f"  Columns -> ZIP: {zc!r} | State: {sc!r} | City: {cc!r} | Name: {nc!r}")
    if not zc and not (cc and sc):
        sys.exit("ERROR: need a ZIP/Postal column, or City + State columns.")
    recs, seen, n_fix = [], set(), 0
    for _, r in df.iterrows():
        raw_zip = str(r[zc]).strip() if zc and pd.notna(r[zc]) else ''
        st  = norm_state(r[sc]) if sc and pd.notna(r[sc]) else ''
        cty = str(r[cc]).replace('\xa0',' ').strip() if cc and pd.notna(r[cc]) else ''
        nm  = str(r[nc]).replace('\xa0',' ').strip() if nc and pd.notna(r[nc]) else ''
        if cty.lower() in ('', 'nan'): cty = ''
        if nm.lower()  in ('', 'nan'): nm  = ''
        if raw_zip.lower() in ('', 'nan'): raw_zip = ''
        if not raw_zip and not (cty and st): continue
        key = (nm.lower(), cty.lower(), st, raw_zip)
        if key in seen: continue
        seen.add(key)
        geo_zip, disp_zip, note = (None, '', '')
        if raw_zip:
            geo_zip, disp_zip, note = repair_zip(raw_zip, st)
            if note: n_fix += 1
        if not st and geo_zip and geo_zip in _ZDB: st = _ZDB[geo_zip][3]
        if not cty and geo_zip: cty = city_from_zip(geo_zip)
        community = nm or (f"{cty}, {st} {disp_zip}".strip() if cty else f"{st} {disp_zip}".strip())
        recs.append({'Community': community, 'City': cty, 'State': st,
                     'ZIP': geo_zip or disp_zip, 'Orig ZIP': disp_zip, 'Note': note})
    out = pd.DataFrame(recs)
    print(f"  Client locations: {len(out)}   (ZIPs corrected/flagged: {n_fix})")
    return out

# ── PROVIDER LOADERS ────────────────────────────────────────────────────────
def find_provider_files(providers_dir, input_path):
    dirs = [d for d in [providers_dir, SAMPLE_DIR, os.path.dirname(os.path.abspath(input_path)), os.getcwd()] if d]
    def find(name):
        for d in dirs:
            p = os.path.join(d, name)
            if os.path.exists(p): return p
        return None
    nol = find("network_sites.csv"); pa = find("partner_a_sites.csv"); pb = find("partner_b_sites.csv")
    missing = [n for n, p in (("network_sites.csv", nol), ("partner_a_sites.csv", pa),
                              ("partner_b_sites.csv", pb)) if not p]
    if missing:
        sys.exit("ERROR: provider file(s) not found: " + ", ".join(missing) +
                 "\n  Looked in: " + " | ".join(dirs) + "\n  Pass --providers-dir <folder>.")
    return nol, pb, pa

def _zip5(series):
    return series.astype(str).str.split('-').str[0].str.split('.').str[0].str.zfill(5)

def load_nol(p):
    df = pd.read_csv(p, dtype=str); df['Zip'] = _zip5(df['Zip'])
    print(f"  NOL (active, full-service): {len(df)}"); return df

def load_partner_b(p):
    df = pd.read_csv(p, dtype=str); df['Zip'] = _zip5(df['Zip'])
    df['display_name'] = df.apply(lambda r: f"Partner B - {str(r['City']).title()}"
        if pd.notna(r['City']) and str(r['City']).strip() else f"Partner B - {r['Zip']}", axis=1)
    print(f"  Partner B: {len(df)}"); return df

def load_partner_a(p):
    df = pd.read_csv(p, dtype=str); df['Zip'] = _zip5(df['Zip'])
    df = df[df['Name'].fillna('').str.strip() != ''].copy()
    print(f"  Partner A: {len(df)}"); return df

def build_loc_list(df, name_col, zip_col, city_col, state_col, addr_col, svc):
    locs = []
    for _, row in df.iterrows():
        c = get_coords(row[zip_col])
        if not c: continue
        def g(col):
            v = row.get(col, ''); return str(v) if (col and pd.notna(v) and str(v) != 'nan') else ''
        locs.append({'zip': clean_zip(row[zip_col]), 'lat': c[0], 'lon': c[1], 'name': g(name_col),
                     'city': g(city_col), 'state': g(state_col), 'address': g(addr_col), 'svc': svc})
    return locs

# ── STYLES ──────────────────────────────────────────────────────────────────
def make_styles():
    thin = Side(style='thin', color='CCCCCC'); med = Side(style='medium', color='1F4E79')
    return {'hdr_fill': PatternFill("solid", fgColor="1F4E79"),
        'hdr_font': Font(bold=True, color="FFFFFF", size=11, name="Arial"),
        'alt': PatternFill("solid", fgColor="F2F7FB"), 'white': PatternFill("solid", fgColor="FFFFFF"),
        'green': PatternFill("solid", fgColor="C6EFCE"), 'nol_alt': PatternFill("solid", fgColor="EBF7EE"),
        'blue': PatternFill("solid", fgColor="DDEBF7"), 'pa_alt': PatternFill("solid", fgColor="EEF4FB"),
        'conly': PatternFill("solid", fgColor="BDD7EE"), 'yellow': PatternFill("solid", fgColor="FFEB9C"),
        'pb_alt': PatternFill("solid", fgColor="FFF7DC"), 'red': PatternFill("solid", fgColor="FFC7CE"),
        'orange': PatternFill("solid", fgColor="FCE4D6"), 'grey': PatternFill("solid", fgColor="E0E0E0"),
        'input': PatternFill("solid", fgColor="FFF9C4"),
        'border': Border(left=thin, right=thin, top=thin, bottom=thin),
        'med_border': Border(left=med, right=med, top=med, bottom=med)}

def cov_fill(val, s):
    v = str(val)
    if v == 'Full NOL Coverage':   return s['green']
    if v == 'Partner A + Partner B': return s['blue']
    if v == 'Partner A Only':      return s['conly']
    if v == 'Partner B Only':        return s['yellow']
    if 'No Coverage' in v:         return s['red']
    return s['white']

def pri_fill(val, s):
    v = str(val)
    for k, f in (('🔴','red'),('🟠','orange'),('🟡','yellow'),('🟢','green')):
        if k in v: return s[f]
    return s['white']

def neighbors(tc, locs):
    return sorted(((haversine(tc[0], tc[1], l['lat'], l['lon']), l) for l in locs), key=lambda x: x[0])

def classify(tc, nol_list, pa_list, pb_list, radius):
    nol = neighbors(tc, nol_list); con = neighbors(tc, pa_list); lc = neighbors(tc, pb_list)
    n_in = [x for x in nol if x[0] <= radius]; c_in = [x for x in con if x[0] <= radius]
    l_in = [x for x in lc if x[0] <= radius]
    if n_in:            cls, pri = 'Full NOL Coverage', 4
    elif c_in and l_in: cls, pri = 'Partner A + Partner B', 3
    elif c_in:          cls, pri = 'Partner A Only', 3
    elif l_in:          cls, pri = 'Partner B Only', 2
    else:               cls, pri = f'No Coverage Within {radius}mi', 1
    priority = {1: f'🔴 High: No provider within {radius}mi',
                2: '🟠 Medium: Partner B only (no full occ-health)',
                3: '🟡 Low: Partial (no full-service NOL)',
                4: f'🟢 Covered: NOL partner within {radius}mi'}[pri]
    return {'cls': cls, 'pri': pri, 'priority': priority, 'nol': nol, 'pa': con, 'pb': lc,
            'n_in': n_in, 'c_in': c_in, 'l_in': l_in}

# ── WRITERS ─────────────────────────────────────────────────────────────────
def style_header(ws, cols, s, row=1):
    for c, col in enumerate(cols, 1):
        cell = ws.cell(row, c, col); cell.fill = s['hdr_fill']; cell.font = s['hdr_font']
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = s['border']

def fmt_closest(item):
    if not item: return '', None
    d, l = item
    return (f"{l['name']} ({l['city']}, {l['state']})" if l.get('city') else l['name']), round(d, 1)

def write_helper_sheet(ws, locs, svc):
    for c, h in enumerate(["Name","Address","City","State","ZIP","Lat","Lon","Services"], 1): ws.cell(1, c, h)
    for r, l in enumerate(locs, 2):
        for c, v in enumerate([l['name'], l['address'], l['city'], l['state'], l['zip'], l['lat'], l['lon'], svc], 1):
            ws.cell(r, c, v)

def write_zip_lookup(ws, nol_d, pa_d, pb_d, s, radius):
    ws['A1'] = "📍 ZIP CODE PROXIMITY LOOKUP"
    ws['A1'].font = Font(bold=True, size=16, color="1F4E79", name="Arial"); ws.merge_cells('A1:I1')
    ws['A2'] = (f"Type a ZIP in the yellow box: results auto-update with the closest {TOP_N} "
                f"NOL, Partner A, and Partner B locations sorted by distance.")
    ws['A2'].font = Font(italic=True, size=10, color="595959", name="Arial"); ws.merge_cells('A2:I2')
    ws['A4'] = "Enter ZIP Code:"; ws['A4'].font = Font(bold=True, size=12, name="Arial")
    ws['B4'].fill = s['input']; ws['B4'].border = s['med_border']
    ws['B4'].font = Font(bold=True, size=14, name="Arial")
    ws['B4'].alignment = Alignment(horizontal="center", vertical="center"); ws['B4'].number_format = '@'
    ws['D4'] = "Max Miles:"; ws['D4'].font = Font(bold=True, size=12, name="Arial")
    ws['E4'] = radius; ws['E4'].fill = s['input']; ws['E4'].border = s['med_border']
    ws['E4'].font = Font(bold=True, size=14, name="Arial"); ws['E4'].alignment = Alignment(horizontal="center", vertical="center")
    ws['A5'] = "ZIP Lat:"; ws['A5'].font = Font(italic=True, size=9, color="888888", name="Arial")
    ws['B5'] = '=IFERROR(VLOOKUP(TEXT(B4,"00000"),_ZIP_C!A:C,2,FALSE),"")'
    ws['D5'] = "ZIP Lon:"; ws['D5'].font = Font(italic=True, size=9, color="888888", name="Arial")
    ws['E5'] = '=IFERROR(VLOOKUP(TEXT(B4,"00000"),_ZIP_C!A:C,3,FALSE),"")'
    ws['G5'] = '=IF(B5="","⚠️ Enter a valid ZIP code above","✅ ZIP found: results below")'
    ws['G5'].font = Font(bold=True, size=10, name="Arial"); ws.merge_cells('G5:I5')
    tmpl = ('=IF(OR($B$5="",$B$5=0),"",3958.8*2*ASIN(SQRT('
            'SIN(RADIANS({s}!F{i}-$B$5)/2)^2+COS(RADIANS($B$5))*COS(RADIANS({s}!F{i}))*'
            'SIN(RADIANS({s}!G{i}-$E$5)/2)^2)))')
    for i in range(1, nol_d + 1): ws.cell(i+1, 11, tmpl.format(s='_NOL_D', i=i+1))
    for i in range(1, pa_d + 1): ws.cell(i+1, 14, tmpl.format(s='_PA_D', i=i+1))
    for i in range(1, pb_d + 1):  ws.cell(i+1, 17, tmpl.format(s='_PB_D', i=i+1))
    rc = ['#', 'Location Name', 'Address', 'City', 'State', 'ZIP', 'Services Offered', 'Distance (Miles)', 'Within Limit?']
    for c, w in enumerate([5, 42, 35, 18, 8, 10, 48, 18, 13], 1): ws.column_dimensions[get_column_letter(c)].width = w
    sections = [
        ("🟩 NOL: Full Service (Urine Collection Capable)", 7, 8, 'K', '_NOL_D', nol_d, s['green'], s['nol_alt']),
        ("🔵 Partner A: All Services Except Blood/Urine", 7+TOP_N+3, 8+TOP_N+3, 'N', '_PA_D', pa_d, s['blue'], s['pa_alt']),
        ("🟨 Partner B: Blood Draw & Urine Collection Only", 7+2*(TOP_N+3), 8+2*(TOP_N+3), 'Q', '_PB_D', pb_d, s['yellow'], s['pb_alt'])]
    for title, tr, hr, dc, ds, dcount, fa, fb in sections:
        ws.cell(tr, 1, title).font = Font(bold=True, size=12, color="1F4E79", name="Arial"); ws.merge_cells(f'A{tr}:I{tr}')
        style_header(ws, rc, s, row=hr)
        for rank in range(1, TOP_N + 1):
            r = hr + rank; ws.cell(r, 1, rank).alignment = Alignment(horizontal="center")
            base = f'MATCH(SMALL({dc}$2:{dc}${dcount+1},{rank}),{dc}$2:{dc}${dcount+1},0)'
            for ci, cl in enumerate(['A', 'B', 'C', 'D', 'E', 'H'], 2):
                ws.cell(r, ci, f'=IFERROR(INDEX({ds}!{cl}$2:{cl}${dcount+1},{base}),"")')
            dcell = ws.cell(r, 8, f'=IFERROR(SMALL({dc}$2:{dc}${dcount+1},{rank}),"")'); dcell.number_format = '0.0'
            ws.cell(r, 9, f'=IFERROR(IF(SMALL({dc}$2:{dc}${dcount+1},{rank})<=$E$4,"✅ Yes","❌ No"),"")')
            for c in range(1, 10):
                cell = ws.cell(r, c); cell.fill = fa if rank % 2 == 1 else fb
                cell.font = Font(name="Arial", size=10); cell.border = s['border']; cell.alignment = Alignment(vertical="center")
    for col in ['J','K','L','M','N','O','P','Q','R']: ws.column_dimensions[col].hidden = True
    ws.row_dimensions[1].height = 26; ws.row_dimensions[4].height = 28

def write_list_sheet(ws, locs, s, fills, note):
    cols = ['Name', 'Address', 'City', 'State', 'ZIP', 'Services Offered']
    ws.cell(1, 1, note).font = Font(italic=True, color="595959", name="Arial", size=10)
    ws.merge_cells(f'A1:{get_column_letter(len(cols))}1'); style_header(ws, cols, s, row=2)
    for r, l in enumerate(locs, 3):
        rf = fills[r % 2]
        for c, v in enumerate([l['name'], l['address'], l['city'], l['state'], l['zip'], l.get('svc', '')], 1):
            cell = ws.cell(r, c, v); cell.fill = rf; cell.border = s['border']
            cell.font = Font(name="Arial", size=10); cell.alignment = Alignment(vertical="center")
    for c, w in enumerate([42, 35, 18, 8, 10, 50], 1): ws.column_dimensions[get_column_letter(c)].width = w
    ws.row_dimensions[2].height = 22; ws.freeze_panes = "A3"; ws.auto_filter.ref = f"A2:{get_column_letter(len(cols))}2"

# ── MAIN ────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description="Build a medical-testing coverage map workbook for a client.")
    ap.add_argument("--input", required=True, help="client location file (xlsx/csv)")
    ap.add_argument("--client", required=True, help="client name (titles + output filename)")
    ap.add_argument("--out", default=None, help="output folder (default: next to input)")
    ap.add_argument("--radius", type=float, default=RADIUS_MILES, help="miles (default 25)")
    ap.add_argument("--providers-dir", default=None, help="folder holding the 3 provider files")
    ap.add_argument("--zip-db", default=None, help="ZIP centroid CSV (zip,lat,lon,city,state)")
    ap.add_argument("--sheet", default=None, help="sheet name in the input workbook")
    ap.add_argument("--date", default=datetime.date.today().strftime("%-m.%-d.%Y"), help="report date label")
    a = ap.parse_args()
    global ZIP_DB_PATH
    if a.zip_db: ZIP_DB_PATH = a.zip_db
    radius = a.radius; client = a.client.strip()
    out_dir = a.out or os.path.dirname(os.path.abspath(a.input)); os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, f"{client}_Coverage Report {a.date}.xlsx")
    s = make_styles()
    print("=" * 60); print(f"{client.upper()}: MEDICAL TESTING COVERAGE MAP  ({radius:g}-mile radius)"); print("=" * 60)

    print("\n[1/5] Loading data..."); _load_zdb()
    df_foot = load_footprint(a.input, a.sheet)
    nol_p, pb_p, pa_p = find_provider_files(a.providers_dir, a.input)
    nol_list = build_loc_list(load_nol(nol_p), 'LocationName', 'Zip', 'CityName', 'StateName', 'Address1', NOL_SVC)
    pa_list = build_loc_list(load_partner_a(pa_p), 'Name', 'Zip', 'City', 'State', 'Address', PA_SVC)
    pb_list  = build_loc_list(load_partner_b(pb_p), 'display_name', 'Zip', 'City', 'State', 'Address1', PB_SVC)
    print(f"  Geocoded: NOL={len(nol_list)} Partner A={len(pa_list)} Partner B={len(pb_list)}")

    print("\n[2/5] Classifying each location...")
    summary_rows, nol_map, pa_map, pb_map = [], [], [], []; n_cityfix = n_unmapped = 0
    for _, row in df_foot.iterrows():
        tc = get_coords(row['ZIP']) if row['ZIP'] else None; geo_note = str(row.get('Note', '') or '')
        if not tc:
            tc = get_coords_city(row['City'], row['State'])
            if tc: geo_note = (geo_note + '; ' if geo_note else '') + 'geo via City/State (check ZIP)'; n_cityfix += 1
        base = {'Community': row['Community'], 'City': row['City'], 'State': row['State'], 'ZIP': row['Orig ZIP']}
        if not tc:
            n_unmapped += 1
            summary_rows.append({**base, 'Coverage Classification': 'ZIP not found',
                f'NOL <={radius:g}mi': '', f'Partner A <={radius:g}mi': '', f'Partner B <={radius:g}mi': '',
                'Closest NOL': '', 'NOL Miles': '', 'Closest Partner A': '', 'Partner A Miles': '',
                'Closest Partner B': '', 'Partner B Miles': '', 'Recruitment Priority': '⚠️ Verify location',
                'Geo Note': geo_note or 'could not geocode', '_pri': 0}); continue
        info = classify(tc, nol_list, pa_list, pb_list, radius)
        n_nm, n_mi = fmt_closest(info['nol'][0] if info['nol'] else None)
        c_nm, c_mi = fmt_closest(info['pa'][0] if info['pa'] else None)
        l_nm, l_mi = fmt_closest(info['pb'][0] if info['pb'] else None)
        summary_rows.append({**base, 'Coverage Classification': info['cls'],
            f'NOL <={radius:g}mi': len(info['n_in']), f'Partner A <={radius:g}mi': len(info['c_in']),
            f'Partner B <={radius:g}mi': len(info['l_in']),
            'Closest NOL': n_nm, 'NOL Miles': n_mi, 'Closest Partner A': c_nm, 'Partner A Miles': c_mi,
            'Closest Partner B': l_nm, 'Partner B Miles': l_mi, 'Recruitment Priority': info['priority'],
            'Geo Note': geo_note, '_pri': info['pri']})
        def emit(target, neigh_in, neigh_all):
            for d, l in (neigh_in if neigh_in else (neigh_all[:1] if neigh_all else [])):
                target.append({'Community': row['Community'], 'Comm City': row['City'], 'Comm State': row['State'],
                    'Comm ZIP': row['Orig ZIP'], 'Provider': l['name'], 'Provider Address': l['address'],
                    'Provider City': l['city'], 'Provider State': l['state'], 'Provider ZIP': l['zip'],
                    'Distance (mi)': round(d, 1),
                    'Status': f'Within {radius:g}mi' if d <= radius else f'⚠️ OUTSIDE {radius:g}mi (closest)'})
        emit(nol_map, info['n_in'], info['nol']); emit(pa_map, info['c_in'], info['pa']); emit(pb_map, info['l_in'], info['pb'])

    df_sum = pd.DataFrame(summary_rows).sort_values(['_pri', 'State', 'Community'], na_position='last').reset_index(drop=True)
    print(f"  Geocoded via City/State fallback: {n_cityfix}   Unmapped: {n_unmapped}")
    print("\n  Coverage breakdown:")
    for cls, cnt in df_sum['Coverage Classification'].value_counts().items(): print(f"    {cls}: {cnt}")

    print("\n[3/5] Building workbook..."); wb = Workbook(); wb.remove(wb.active)
    ws = wb.create_sheet("Coverage Summary")
    cnt_cols = [f'NOL <={radius:g}mi', f'Partner A <={radius:g}mi', f'Partner B <={radius:g}mi']
    sum_cols = ['Community', 'City', 'State', 'ZIP', 'Coverage Classification', 'Recruitment Priority', *cnt_cols,
                'Closest NOL', 'NOL Miles', 'Closest Partner A', 'Partner A Miles', 'Closest Partner B', 'Partner B Miles', 'Geo Note']
    ws.cell(1, 1, f"{client.upper()}: MEDICAL TESTING COVERAGE  ·  {len(df_sum)} locations  ·  "
                  f"{radius:g}-mile radius  ·  sorted by coverage gap (worst first)").font = Font(bold=True, color="1F4E79", name="Arial", size=11)
    ws.merge_cells(f'A1:{get_column_letter(len(sum_cols))}1'); style_header(ws, sum_cols, s, row=2)
    for r, rd in enumerate(df_sum.fillna('').to_dict('records'), 3):
        rf = s['alt'] if r % 2 == 0 else s['white']
        for c, col in enumerate(sum_cols, 1):
            val = rd.get(col, ''); cell = ws.cell(r, c, val if val != '' else '')
            cell.border = s['border']; cell.font = Font(name="Arial", size=10); cell.alignment = Alignment(vertical="center")
            if col == 'ZIP': cell.number_format = '@'
            if col == 'Coverage Classification':
                cell.fill = cov_fill(val, s); cell.font = Font(bold=True, name="Arial", size=10)
                cell.alignment = Alignment(horizontal="center", vertical="center")
            elif col == 'Recruitment Priority': cell.fill = pri_fill(val, s)
            elif col in cnt_cols:
                zero = isinstance(val, int) and val == 0
                cell.fill = s['red'] if zero else rf; cell.alignment = Alignment(horizontal="center", vertical="center")
                if zero: cell.font = Font(bold=True, name="Arial", size=10)
            elif col in ('NOL Miles', 'Partner A Miles', 'Partner B Miles'):
                far = isinstance(val, (int, float)) and val > radius
                cell.fill = s['orange'] if far else rf; cell.alignment = Alignment(horizontal="center", vertical="center")
                if far: cell.font = Font(bold=True, name="Arial", size=10)
            else: cell.fill = rf
        ws.row_dimensions[r].height = 24
    widths = {'Community': 40, 'City': 16, 'State': 7, 'ZIP': 10, 'Coverage Classification': 24, 'Recruitment Priority': 36,
              cnt_cols[0]: 11, cnt_cols[1]: 14, cnt_cols[2]: 12, 'Closest NOL': 40, 'NOL Miles': 10,
              'Closest Partner A': 40, 'Partner A Miles': 13, 'Closest Partner B': 40, 'Partner B Miles': 11, 'Geo Note': 40}
    for c, col in enumerate(sum_cols, 1): ws.column_dimensions[get_column_letter(c)].width = widths.get(col, 14)
    ws.row_dimensions[2].height = 30; ws.freeze_panes = "B3"; ws.auto_filter.ref = f"A2:{get_column_letter(len(sum_cols))}2"

    map_cols = ['Community', 'Comm City', 'Comm State', 'Comm ZIP', 'Provider', 'Provider Address', 'Provider City',
                'Provider State', 'Provider ZIP', 'Distance (mi)', 'Status']
    def write_map(title, rows, fills):
        wsm = wb.create_sheet(title)
        df = (pd.DataFrame(rows) if rows else pd.DataFrame(columns=map_cols)).sort_values(['Community', 'Distance (mi)']).reset_index(drop=True)
        wsm.cell(1, 1, f"{title}: every provider within {radius:g} miles of each location. "
                       f"Locations with none in range show their single CLOSEST (flagged ⚠️).").font = Font(italic=True, color="595959", name="Arial", size=10)
        wsm.merge_cells(f'A1:{get_column_letter(len(map_cols))}1'); style_header(wsm, map_cols, s, row=2)
        for r, rd in enumerate(df.fillna('').to_dict('records'), 3):
            outside = '⚠️' in str(rd.get('Status', '')); rf = fills[r % 2]
            for c, col in enumerate(map_cols, 1):
                cell = wsm.cell(r, c, rd.get(col, '')); cell.border = s['border']
                cell.font = Font(name="Arial", size=10); cell.alignment = Alignment(vertical="center")
                if col in ('Comm ZIP', 'Provider ZIP'): cell.number_format = '@'
                if col == 'Status':
                    cell.fill = s['orange'] if outside else s['green']; cell.alignment = Alignment(horizontal="center", vertical="center")
                elif col == 'Distance (mi)':
                    cell.fill = s['orange'] if outside else rf; cell.alignment = Alignment(horizontal="center", vertical="center")
                else: cell.fill = rf
        for c, w in enumerate([40, 16, 9, 10, 36, 34, 16, 9, 10, 12, 24], 1): wsm.column_dimensions[get_column_letter(c)].width = w
        wsm.row_dimensions[2].height = 22; wsm.freeze_panes = "A3"; wsm.auto_filter.ref = f"A2:{get_column_letter(len(map_cols))}2"
        print(f"  {title}: {len(df)} rows")
    rl = f"(<={radius:g}mi)"
    write_map(f"NOL Mapping {rl}", nol_map, {0: s['nol_alt'], 1: s['white']})
    write_map(f"Partner A Mapping {rl}", pa_map, {0: s['pa_alt'], 1: s['white']})
    write_map(f"Partner B Mapping {rl}", pb_map, {0: s['pb_alt'], 1: s['white']})

    print("\n[4/5] ZIP Lookup + helpers...")
    ws_z = wb.create_sheet("_ZIP_C"); ws_z.sheet_state = 'hidden'
    ws_z.cell(1, 1, "ZIP"); ws_z.cell(1, 2, "Lat"); ws_z.cell(1, 3, "Lon")
    for r, (z, (la, lo, _, _)) in enumerate(sorted(_ZDB.items()), 2):
        ws_z.cell(r, 1, z); ws_z.cell(r, 2, la); ws_z.cell(r, 3, lo)
    for nm, lst, svc in (("_NOL_D", nol_list, NOL_SVC), ("_PA_D", pa_list, PA_SVC), ("_PB_D", pb_list, PB_SVC)):
        wsh = wb.create_sheet(nm); wsh.sheet_state = 'hidden'; write_helper_sheet(wsh, lst, svc)
    write_zip_lookup(wb.create_sheet("ZIP Lookup"), len(nol_list), len(pa_list), len(pb_list), s, radius)

    print("\n[5/5] Reference lists...")
    write_list_sheet(wb.create_sheet("NOL Full List"), nol_list, s, {0: s['nol_alt'], 1: s['green']},
                     f"NOL: full service ({len(nol_list)}). Source: {os.path.basename(nol_p)}")
    write_list_sheet(wb.create_sheet("Partner A Full List"), pa_list, s, {0: s['pa_alt'], 1: s['blue']},
                     f"Partner A: all occ health EXCEPT blood/urine ({len(pa_list)}). Source: {os.path.basename(pa_p)}")
    write_list_sheet(wb.create_sheet("Partner B Full List"), pb_list, s, {0: s['pb_alt'], 1: s['yellow']},
                     f"Partner B: blood draw & urine ONLY ({len(pb_list)}). Source: {os.path.basename(pb_p)}")
    front = ["Coverage Summary", f"NOL Mapping {rl}", f"Partner A Mapping {rl}", f"Partner B Mapping {rl}",
             "ZIP Lookup", "NOL Full List", "Partner A Full List", "Partner B Full List"]
    for tab in reversed(front):
        if tab in wb.sheetnames: wb._sheets.insert(0, wb._sheets.pop(wb.sheetnames.index(tab)))
    wb.save(out_file)
    print(f"\n{'=' * 60}\nCOMPLETE → {out_file}\n  {len(wb.sheetnames)} tabs · {len(df_sum)} locations\n{'=' * 60}")
    return out_file

if __name__ == "__main__":
    main()
