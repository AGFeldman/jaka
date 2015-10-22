'''
Run with 'python caseX.py > caseX.json'
'''

import json

description = [
    {'id': 'R1'},
    {'id': 'R2'},
    {'id': 'R3'},
    {'id': 'R4'},
    {'id': 'H1'},
    {'id': 'H2'},
    {
        'id': 'L0',
        'endpoints': ['H1', 'R1'],
        'rate': 12.5 * 10**6,
        'delay': 10 * 10**-3,
        'buffer': 64 * 10**3
        },
    {
        'id': 'L1',
        'endpoints': ['R1', 'R2'],
        'rate': 10 * 10**6,
        'delay': 10 * 10**-3,
        'buffer': 64 * 10**3
        },
    {
        'id': 'L2',
        'endpoints': ['R1', 'R3'],
        'rate': 10 * 10**6,
        'delay': 10 * 10**-3,
        'buffer': 64 * 10**3
        },
    {
        'id': 'L3',
        'endpoints': ['R2', 'R4'],
        'rate': 10 * 10**6,
        'delay': 10 * 10**-3,
        'buffer': 64 * 10**3
        },
    {
        'id': 'L4',
        'endpoints': ['R3', 'R4'],
        'rate': 10 * 10**6,
        'delay': 10 * 10**-3,
        'buffer': 64 * 10**3
        },
    {
        'id': 'L5',
        'endpoints': ['R4', 'H2'],
        'rate': 12.5 * 10**6,
        'delay': 10 * 10**-3,
        'buffer': 64 * 10**3
        },
    {'id': 'F1', 'src': 'H1', 'dst': 'H2', 'amount': 20 * 10**6, 'start': 0.5},
    ]

print json.dumps(description)
