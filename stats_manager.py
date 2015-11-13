import globals_

from graph import Graph
from matplotlib.backends.backend_pdf import PdfPages


class StatsManager(object):
    '''
    To be used as a singleton.
    The StatsManager is responsible for aggregation
    of data. Objects call the notify method with a
    Datum object as argument.
    '''

    def __init__(self):
        self.graphs = dict()
        self.tag_count = 0
        self.pdfpages = PdfPages('todoagf_output.pdf')  # TODO(agf)

    def new_graph(self, **kwargs):
        '''
        Creates a new receiver within the StatsManager.
        Returns a tag which will be used to identify
        Datum objects with the receiver.
        '''
        print kwargs
        g = Graph(**kwargs)
        tag = self.tag_count
        # Ensure tags are unique
        self.tag_count += 1
        self.graphs[tag] = g
        return tag

    def notify(self, tag, value):
        '''
        Receives a tag and value from another object.
        Associates the value with the graph specified
        by the tag.
        '''
        time = globals_.event_manager.get_time()
        self.graphs[tag].append(time, value)

    def output_graphs(self):
        '''
        Outputs all of the graphs from the generated
        data
        '''
        for tag, graph in self.graphs.iteritems():
            graph.draw()
            self.pdfpages.savefig()
        self.pdfpages.close()
