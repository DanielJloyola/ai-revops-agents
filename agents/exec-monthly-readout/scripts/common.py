"""Shared helpers for the exec monthly readout pull scripts (dynamic / live)."""
import datetime, glob, json, os, re, sys

def parse_month(s=None):
    """'2026-10' / '202610' / blank / 'prev' -> (year, month). Blank = previous calendar month."""
    if not s or s.strip().lower() in ('prev', 'previous', 'last', 'last-month'):
        t = datetime.date.today().replace(day=1) - datetime.timedelta(days=1)
        return t.year, t.month
    m = re.fullmatch(r'(\d{4})-?(0[1-9]|1[0-2]|[1-9])', s.strip())
    if not m: sys.exit(f'month must look like 2026-10 (or blank for the previous calendar month), got {s}')
    return int(m.group(1)), int(m.group(2))

def month_window(year, m):
    start = datetime.date(year, m, 1)
    end = datetime.date(year + 1, 1, 1) if m == 12 else datetime.date(year, m + 1, 1)
    return start, end   # [start, end)

def et_window(year, m):
    """The month's [start, end) as UTC instants of Eastern-time midnights, for SOQL
    datetime filters. The org reports in America/New_York; DST handled by zoneinfo."""
    from zoneinfo import ZoneInfo
    s, e = month_window(year, m)
    et = ZoneInfo('America/New_York')
    def z(d):
        return datetime.datetime(d.year, d.month, d.day, tzinfo=et).astimezone(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    return z(s), z(e)

def prior_month(year, m):  return (year - 1, 12) if m == 1 else (year, m - 1)
def prior_year(year, m):   return (year - 1, m)

def tag(year, m):   return f'{year}m{m:02d}'
def label(year, m): return datetime.date(year, m, 1).strftime('%b %Y')

def workdir(year, m):
    d = f'/home/claude/readout/{year}-{m:02d}'
    os.makedirs(f'{d}/pages', exist_ok=True); os.makedirs(f'{d}/out', exist_ok=True)
    return d

def flatten(r):
    o = {}
    for k, v in r.items():
        if k == 'attributes': continue
        if isinstance(v, dict):
            for kk, vv in v.items():
                if kk != 'attributes': o[f'{k}.{kk}'] = vv
        else: o[k] = v
    return o

def load_pages(wd, ds):
    recs = []
    for p in sorted(glob.glob(f'{wd}/pages/{ds}_*.json')):
        recs += json.load(open(p))
    ids = [r['Id'] for r in recs]
    if len(ids) != len(set(ids)): sys.exit(f'{ds}: duplicate Ids across pages: a page was ingested twice')
    return [flatten(r) for r in recs]

def load_agg(wd, name):
    p = f'{wd}/pages/agg_{name}.json'
    if not os.path.exists(p): return None
    d = json.load(open(p))
    if isinstance(d, list) and d and 'text' in d[0]: d = json.loads(d[0]['text'])
    return d['records']

def pullstamp():
    """Live pull: stamp with date AND time (UTC): the same month can be pulled more than once."""
    return datetime.datetime.utcnow().strftime('%Y-%m-%d_%H%MZ')

def base_datasets(year, m):
    t = tag(year, m)
    return [f'lead_{t}', f'opp_created_{t}', f'opp_closed_{t}']

def present_datasets(wd):
    """Every dataset that has saved pages (comparison detail pulls are optional)."""
    seen = []
    for p in sorted(glob.glob(f'{wd}/pages/*_[0-9][0-9][0-9].json')):
        ds = os.path.basename(p).rsplit('_', 1)[0]
        if ds != 'schema' and ds not in seen: seen.append(ds)
    return seen

def ds_period(ds):
    """'lead_2026m10' -> (2026, 10)."""
    m = re.search(r'_(\d{4})m(\d{2})$', ds)
    return (int(m.group(1)), int(m.group(2))) if m else (None, None)
