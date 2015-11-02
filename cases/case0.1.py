'''
Run with 'python caseX.py > caseX.json'
'''

import json

description = [
    {'id': 'H1', 'type': 'host'},
    {'id': 'R1', 'type': 'router'},
    {'id': 'H2', 'type': 'host'},
    {
        'id': 'L1',
        'type': 'link',
        'endpoints': ['H1', 'R1'],
        'rate': 10 * 10**6,
        'delay': 10 * 10**-3,
        'buffer': 64 * 10**3 * 8
        },
    {
        'id': 'L2',
        'type': 'link',
        'endpoints': ['R1', 'H2'],
        'rate': 10 * 10**6,
        'delay': 10 * 10**-3,
        'buffer': 64 * 10**3 * 8
        },
    {'id': 'F1', 'type': 'flow', 'src': 'H1', 'dst': 'H2', 'amount': 20 * 10**6 * 8, 'start': 1},
    ]

print json.dumps(description)
