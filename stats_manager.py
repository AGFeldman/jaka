import globals_

from graph import Graph

class Datum(object):
    '''
    The datum object has two values:
       tag - The unique graph identifier returned
             by StatsManager.new_graph
       value - The value of the statistic being logged.
    '''

    def __init__(self, tag, value):
        self.tag = tag
        self.value = value

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

    def new_graph(self):
        '''
        Creates a new receiver within the StatsManager.
        Returns a tag which will be used to identify
        Datum objects with the receiver.
        '''
        g = Graph()
        tag = self.tag_count
        # Ensure tags are unique
        self.tag_count += 1
        self.graphs[tag] = g
        return tag

    def notify (self, datum):
        '''
        Receives a datum from another object.
        Associates the value with the graph
        specified by the tag.
        '''
        time = globals_.event_manager.get_time()
        self.graphs[datum.tag].append(time, datum.value)
