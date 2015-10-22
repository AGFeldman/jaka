'''
Run with 'python caseX.py > caseX.json'
'''

import json

description = [
    {'id': 'S1'},
    {'id': 'S2'},
    {'id': 'S3'},
    {'id': 'T1'},
    {'id': 'T2'},
    {'id': 'T3'},
    {'id': 'R1'},
    {'id': 'R2'},
    {'id': 'R3'},
    {'id': 'R4'},
    {
        'id': 'L1',
        'endpoints': ['R1', 'R2'],
        'rate': 10 * 10**6,
        'delay': 10 * 10**-3,
        'buffer': 128 * 10**3
        },
    {
        'id': 'L2',
        'endpoints': ['R2', 'R3'],
        'rate': 10 * 10**6,
        'delay': 10 * 10**-3,
        'buffer': 128 * 10**3
        },
    {
        'id': 'L3',
        'endpoints': ['R3', 'R4'],
        'rate': 10 * 10**6,
        'delay': 10 * 10**-3,
        'buffer': 128 * 10**3
        },
    {
        'id': 'L4',
        'endpoints': ['R1', 'S2'],
        'rate': 12.5 * 10**6,
        'delay': 10 * 10**-3,
        'buffer': 128 * 10**3
        },
    {
        'id': 'L5',
        'endpoints': ['R2', 'T2'],
        'rate': 12.5 * 10**6,
        'delay': 10 * 10**-3,
        'buffer': 128 * 10**3
        },
    {
        'id': 'L6',
        'endpoints': ['R3', 'S3'],
        'rate': 12.5 * 10**6,
        'delay': 10 * 10**-3,
        'buffer': 128 * 10**3
        },
    {
        'id': 'L7',
        'endpoints': ['R4', 'T1'],
        'rate': 12.5 * 10**6,
        'delay': 10 * 10**-3,
        'buffer': 128 * 10**3
        },
    {
        'id': 'L8',
        'endpoints': ['R1', 'S1'],
        'rate': 12.5 * 10**6,
        'delay': 10 * 10**-3,
        'buffer': 128 * 10**3
        },
    {
        'id': 'L9',
        'endpoints': ['R4', 'T3'],
        'rate': 12.5 * 10**6,
        'delay': 10 * 10**-3,
        'buffer': 128 * 10**3
        },
    {'id': 'F1', 'src': 'S1', 'dst': 'T1', 'amount': 35 * 10**6, 'start': 0.5},
    {'id': 'F2', 'src': 'S2', 'dst': 'T2', 'amount': 15 * 10**6, 'start': 10},
    {'id': 'F3', 'src': 'S3', 'dst': 'T3', 'amount': 30 * 10**6, 'start': 20},
    ]

print json.dumps(description)
