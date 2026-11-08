"""Shared helpers for the marketing-recap pull scripts."""
import datetime, glob, json, os, re, sys

def parse_quarter(s):
    m = re.fullmatch(r'(\d{4})-?Q([1-4])', s.strip().upper())
    if not m: sys.exit(f'quarter must look like 2026-Q3, got {s}')
    return int(m.group(1)), int(m.group(2))

def window(year, q):
    start = datetime.date(year, 3*(q-1)+1, 1)
    end = datetime.date(year+1, 1, 1) if q == 4 else datetime.date(year, 3*q+1, 1)
    return start, end   # [start, end)

def tags(year, q):
    return f'{year}q{q}', f'{year-1}q{q}'   # current, prior-year

def workdir(year, q):
    d = f'/home/claude/recap/{year}-Q{q}'
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

def pulldate():
    return datetime.date.today().isoformat()

def datasets(year, q):
    cur, prev = tags(year, q)
    return [f'lead_{cur}', f'lead_{prev}', f'opp_created_{cur}', f'opp_closed_{cur}', f'opp_created_{prev}', f'opp_closed_{prev}']
