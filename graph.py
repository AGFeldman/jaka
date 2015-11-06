import matplotlib.pyplot as plt

class Graph(object):
    '''
    Stores all the information about a graph.
    '''
    def __init__(self):
        self.times = []
        self.values = []

    def draw(self):
        plt.plot(self.times, self.values)
        plt.show()

    def append(self, time, value):
        self.times.append(time)
        self.values.append(value)
