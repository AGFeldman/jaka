'''
Run with 'python check_json.py < cases/case0.json'
'''


import json
import sys


def check(entity_list):
    links = [e for e in entity_list if e['type'] == 'link']
    hosts = [e for e in entity_list if e['type'] == 'host']
    routers = [e for e in entity_list if e['type'] == 'router']
    flows = [e for e in entity_list if e['type'] == 'flow']

    assert len(entity_list) == len(links) + len(hosts) + len(routers) + len(flows)

    def ids(mylist):
        return [x['id'] for x in mylist]

    # List of ids for all hosts and routers
    hr_ids = ids(hosts) + ids(routers)

    # Create a set of all link endpoints
    endpoints = []
    for l in links:
        endpoints += l['endpoints']
    endpoints = set(endpoints)

    # Links should have 6 fields: id, type, endpoints, rate, delay, and buffer
    for l in links:
        assert len(l) == 6
        assert len(l['endpoints']) == 2
        e0, e1 = l['endpoints']
        assert e0 in hr_ids and e1 in hr_ids
        assert l['rate'] >= 0
        assert l['delay'] >= 0
        assert l['buffer'] >= 0

    # Hosts should have 2 fields: id and type
    for h in hosts:
        assert len(h) == 2
        assert h['id'] in endpoints

    # Routers should have 2 fields: id and type
    for r in routers:
        assert len(r) == 2
        assert r['id'] in endpoints

    # Flows should have 7 or 8 fields: id, type, src, dst, amount, start,
    # protocol, and optionally alpha
    for f in flows:
        if f['protocol'] == 'FAST':
            assert len(f) == 8
            assert f['alpha'] >= 0
        else:
            assert len(f) == 7
        assert f['src'] in hr_ids
        assert f['dst'] in hr_ids
        assert f['amount'] >= 0
        assert f['start'] >= 0
        assert f['protocol'] in ('RENO', 'FAST')


if __name__ == '__main__':
    entity_list = json.loads(sys.stdin.read())
    check(entity_list)
