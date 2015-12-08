'''
Run with 'python caseX.py > caseX.json'
'''

import json

description = [
    {'id': 'R1', 'type': 'router'},
    {'id': 'R2', 'type': 'router'},
    {'id': 'R3', 'type': 'router'},
    {'id': 'R4', 'type': 'router'},
    {'id': 'H1', 'type': 'host'},
    {'id': 'H2', 'type': 'host'},
    {
        'id': 'L0',
        'type': 'link',
        'endpoints': ['H1', 'R1'],
        'rate': 12.5 * 10**6,
        'delay': 10 * 10**-3,
        'buffer': 64 * 10**3 * 8
        },
    {
        'id': 'L1',
        'type': 'link',
        'endpoints': ['R1', 'R2'],
        'rate': 10 * 10**6,
        'delay': 10 * 10**-3,
        'buffer': 64 * 10**3 * 8
        },
    {
        'id': 'L2',
        'type': 'link',
        'endpoints': ['R1', 'R3'],
        'rate': 10 * 10**6,
        'delay': 10 * 10**-3,
        'buffer': 64 * 10**3 * 8
        },
    {
        'id': 'L3',
        'type': 'link',
        'endpoints': ['R2', 'R4'],
        'rate': 10 * 10**6,
        'delay': 10 * 10**-3,
        'buffer': 64 * 10**3 * 8
        },
    {
        'id': 'L4',
        'type': 'link',
        'endpoints': ['R3', 'R4'],
        'rate': 10 * 10**6,
        'delay': 10 * 10**-3,
        'buffer': 64 * 10**3 * 8
        },
    {
        'id': 'L5',
        'type': 'link',
        'endpoints': ['R4', 'H2'],
        'rate': 12.5 * 10**6,
        'delay': 10 * 10**-3,
        'buffer': 64 * 10**3 * 8
        },
    {
        'id': 'F1',
        'type': 'flow',
        'src': 'H1',
        'dst': 'H2',
        'amount': 20 * 10**6 * 8,
        'start': 0.5,
        'protocol': 'FAST',
        'alpha': 40
        },
    ]

print json.dumps(description)
