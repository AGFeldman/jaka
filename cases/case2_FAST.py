'''
Run with 'python caseX.py > caseX.json'
'''

import json

description = [
    {'id': 'S1', 'type': 'host'},
    {'id': 'S2', 'type': 'host'},
    {'id': 'S3', 'type': 'host'},
    {'id': 'T1', 'type': 'host'},
    {'id': 'T2', 'type': 'host'},
    {'id': 'T3', 'type': 'host'},
    {'id': 'R1', 'type': 'router'},
    {'id': 'R2', 'type': 'router'},
    {'id': 'R3', 'type': 'router'},
    {'id': 'R4', 'type': 'router'},
    {
        'id': 'L1',
        'type': 'link',
        'endpoints': ['R1', 'R2'],
        'rate': 10 * 10**6,
        'delay': 10 * 10**-3,
        'buffer': 128 * 10**3 * 8
        },
    {
        'id': 'L2',
        'type': 'link',
        'endpoints': ['R2', 'R3'],
        'rate': 10 * 10**6,
        'delay': 10 * 10**-3,
        'buffer': 128 * 10**3 * 8
        },
    {
        'id': 'L3',
        'type': 'link',
        'endpoints': ['R3', 'R4'],
        'rate': 10 * 10**6,
        'delay': 10 * 10**-3,
        'buffer': 128 * 10**3 * 8
        },
    {
        'id': 'L4',
        'type': 'link',
        'endpoints': ['R1', 'S2'],
        'rate': 12.5 * 10**6,
        'delay': 10 * 10**-3,
        'buffer': 128 * 10**3 * 8
        },
    {
        'id': 'L5',
        'type': 'link',
        'endpoints': ['R2', 'T2'],
        'rate': 12.5 * 10**6,
        'delay': 10 * 10**-3,
        'buffer': 128 * 10**3 * 8
        },
    {
        'id': 'L6',
        'type': 'link',
        'endpoints': ['R3', 'S3'],
        'rate': 12.5 * 10**6,
        'delay': 10 * 10**-3,
        'buffer': 128 * 10**3 * 8
        },
    {
        'id': 'L7',
        'type': 'link',
        'endpoints': ['R4', 'T1'],
        'rate': 12.5 * 10**6,
        'delay': 10 * 10**-3,
        'buffer': 128 * 10**3 * 8
        },
    {
        'id': 'L8',
        'type': 'link',
        'endpoints': ['R1', 'S1'],
        'rate': 12.5 * 10**6,
        'delay': 10 * 10**-3,
        'buffer': 128 * 10**3 * 8
        },
    {
        'id': 'L9',
        'type': 'link',
        'endpoints': ['R4', 'T3'],
        'rate': 12.5 * 10**6,
        'delay': 10 * 10**-3,
        'buffer': 128 * 10**3 * 8
        },
    {'id': 'F1', 'type': 'flow', 'src': 'S1', 'dst': 'T1', 'amount': 35 * 10**6 * 8,
        'start': 0.5, 'protocol': 'FAST'},
    {'id': 'F2', 'type': 'flow', 'src': 'S2', 'dst': 'T2', 'amount': 15 * 10**6 * 8,
        'start': 10, 'protocol': 'FAST'},
    {'id': 'F3', 'type': 'flow', 'src': 'S3', 'dst': 'T3', 'amount': 30 * 10**6 * 8,
        'start': 20, 'protocol': 'FAST'},
    ]

print json.dumps(description)
