import sys
from file_parser import FileParser
from main_setup import main_setup


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print "Usage: %s test_file.json" % sys.argv[0]
        sys.exit(-1)

    main_setup()

    file_parser = FileParser()
    network = file_parser.create_network(sys.argv[1])
    network.print_dot()
