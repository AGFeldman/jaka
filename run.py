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


def main_setup(output_name):
    '''
    This should be called at the beginning of main if you're running unit tests
    or simulations.
    It seeds the random number generator and sets the global variable
    |globals_.event_manager|.
    We need to set |globals_.event_manager| for most class definitions and helper
    functions to make sense.
    '''
    random.seed(0)
    globals_.event_manager = EventManager(output_name)
    globals_.stats_manager = StatsManager(output_name)

if __name__ == '__main__':
    if len(sys.argv) != 2 and len(sys.argv) != 3:
        print 'Usage: %s test_file.json [output_name]' % sys.argv[0]
        sys.exit(-1)

    test_case_name = sys.argv[1]
    output_name = 'output'
    if len(sys.argv) > 2:
        output_name = sys.argv[2]

    main_setup(output_name)
    file_parser = FileParser()
    network = file_parser.create_network(test_case_name)
    simulate(network)
    globals_.stats_manager.output_graphs()
