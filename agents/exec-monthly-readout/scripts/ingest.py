"""Save one connector result page. Usage:
  python ingest.py <dataset> <tool_result.json> [--month 2026-10] [--filter ids=Id1,Id2]
  python ingest.py schema <tool_result.json> --month 2026-10
The month defaults to the only directory under /home/claude/readout/."""
import json, sys, glob, os, argparse
ap = argparse.ArgumentParser(); ap.add_argument('dataset'); ap.add_argument('src'); ap.add_argument('--month'); ap.add_argument('--filter')
a = ap.parse_args()
if a.month:
    from common import parse_month
    y, m = parse_month(a.month); wd = f'/home/claude/readout/{y}-{m:02d}'
else:
    ds = glob.glob('/home/claude/readout/*')
    if len(ds) != 1: sys.exit('pass --month; found ' + str(ds))
    wd = ds[0]
os.makedirs(f'{wd}/pages', exist_ok=True)
d = json.load(open(a.src)); s = json.loads(d[0]['text']) if isinstance(d, list) and 'text' in d[0] else d
if a.dataset == 'schema':
    json.dump(s, open(f'{wd}/pages/schema.json', 'w')); print('schema saved', [o['name'] for o in s['details']]); sys.exit()
recs = s['records']
if a.filter and a.filter.startswith('ids='):
    keep = set(a.filter[4:].split(',')); recs = [r for r in recs if r['Id'] in keep]
n = len(glob.glob(f'{wd}/pages/{a.dataset}_*.json'))
json.dump(recs, open(f'{wd}/pages/{a.dataset}_{n:03d}.json', 'w'))
print(json.dumps({'dataset': a.dataset, 'page': n, 'rows': len(recs), 'lastId': recs[-1]['Id'] if recs else None, 'more_pages_likely': len(recs) == 200}))
