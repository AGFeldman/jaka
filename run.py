import random
import sys
import json

import globals_

from event_manager import EventManager
from network import Network
from file_parser import FileParser

'''
    actors = hosts_and_routers.values() + links
    return actors, flows
'''

def simulate(network):
    '''
    Takes a network.
    Runs the simulation!
    '''
    actors = network.getActors()
    flows = network.getFlows()
    globals_.event_manager.set_actors(actors)
    for flow in flows:
        flow.schedule_with_event_manager()
    globals_.event_manager.run()


def main_setup():
    '''
    This should be called at the beginning of main if you're running unit tests
    or simulations.
    It seeds the random number generator and sets the global variable
    |globals_.event_manager|.
    We need to set |globals_.event_manager| for most class definitions and helper
    functions to make sense.
    '''
    random.seed(0)
    globals_.event_manager = EventManager()

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print "Usage: %s test_file.json" % sys.argv[0]
        sys.exit(-1)

    main_setup()
    file_parser = FileParser()
    network = file_parser.create_network(sys.argv[1])
    simulate(network)
    #simulate(sys.stdin.read())
