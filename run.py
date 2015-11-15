import sys

import globals_

from file_parser import FileParser
from main_setup import main_setup


def simulate(network):
    '''
    Takes a network.
    Runs the simulation!
    '''
    globals_.event_manager.register_network(network)
    globals_.event_manager.run()


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
