import random
import sys

import globals_

from event_manager import EventManager
from stats_manager import StatsManager
from file_parser import FileParser


def simulate(network):
    '''
    Takes a network.
    Runs the simulation!
    '''
    globals_.event_manager.register_network(network)
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
    globals_.stats_manager = StatsManager()

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print "Usage: %s test_file.json" % sys.argv[0]
        sys.exit(-1)

    main_setup()
    file_parser = FileParser()
    network = file_parser.create_network(sys.argv[1])
    simulate(network)
