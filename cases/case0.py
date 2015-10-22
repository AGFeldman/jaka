'''
Run with 'python caseX.py > caseX.json'
'''

import json

description = [
    {'id': 'H1'},
    {'id': 'H2'},
    {'id': 'L1', 'endpoints': ['H1', 'H2'], 'rate': 10 * 10**6, 'delay': 10 * 10**-3, 'buffer': 64 * 10**3},
    {'id': 'F1', 'src': 'H1', 'dst': 'H2', 'amount': 20 * 10**6, 'start': 1},
    ]

print json.dumps(description)
