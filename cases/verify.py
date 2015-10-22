'''
Run with 'python verify.py < case0.json'
'''

import json
import sys

description = json.loads(sys.stdin.read())

def filter_by_first_letter(first_letter):
    return [e for e in description if e['id'][0] == first_letter]

def ids(mylist):
    return [x['id'] for x in mylist]

links = filter_by_first_letter('L')
hosts = filter_by_first_letter('H') + filter_by_first_letter('S') + filter_by_first_letter('T')
routers = filter_by_first_letter('R')
flows = filter_by_first_letter('F')

# List of ids for all hosts and routers
hrs_ids = ids(hosts) + ids(routers)

# Create a set of all link endpoints
endpoints = []
for l in links:
    endpoints += l['endpoints']
endpoints = set(endpoints)

assert len(description) == len(links) + len(hosts) + len(routers) + len(flows)

# Links should have 5 fields: id, endpoints, rate, delay, and buffer
for l in links:
    assert len(l) == 5
    assert len(l['endpoints']) == 2
    e0, e1 = l['endpoints']
    assert e0 in hrs_ids and e1 in hrs_ids
    assert l['rate'] >= 0
    assert l['delay'] >= 0
    assert l['buffer'] >= 0

# Hosts should have 1 field: id
for h in hosts:
    assert len(h) == 1
    assert h['id'] in endpoints

# Routers should have 1 field: id
for r in routers:
    assert len(r) == 1
    assert r['id'] in endpoints

# Flows should have 5 fields: id, src, dst, amount, and start
for f in flows:
    assert len(f) == 5
    assert f['src'] in hrs_ids
    assert f['dst'] in hrs_ids
    assert f['amount'] >= 0
    assert f['start'] >= 0
