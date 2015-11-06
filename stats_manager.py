import globals_

from graph import Graph


class StatsManager(object):
    '''
    To be used as a singleton.
    The StatsManager is responsible for aggregation
    of data. Objects call the notify method with a
    Datum object as argument.
    '''

    def __init__(self):
        self.graphs = dict()
        self.tag_count = 0;

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

    def notify (self, tag, value):
        '''
        Receives a tag and value from another object.
        Associates the value with the graph specified
        by the tag.
        '''
        time = globals_.event_manager.get_time()
        self.graphs[tag].append(time, value)

    def output_graphs (self, display=False):
        '''
        Outputs all of the graphs from the generated
        data
        '''
        for tag, graph in self.graphs.iteritems():
            # TODO(keegan): Save as file name specific to case
            # and with more descriptive file name
            graph.draw(display=display,
                       filename="output/out_{}.png".format(tag))
