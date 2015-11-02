import sys
from file_parser import FileParser

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print "Usage: %s test_file.json" % sys.argv[0]
        sys.exit(-1)

    file_parser = FileParser()
    network = file_parser.create_network(sys.argv[1])
    network.print_dot()
