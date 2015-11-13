import matplotlib.pyplot as plt


class Graph(object):
    '''
    Stores all the information about a graph.
    '''

    def __init__(self, title=None, ylabel=None):
        self.title = title
        self.ylabel = ylabel
        self.times = []
        self.values = []

    def draw(self):
        fig = plt.figure()
        ax = fig.add_subplot(111)
        if self.title:
            ax.set_title(self.title)
        if self.ylabel:
            ax.set_ylabel(self.ylabel)
        ax.set_xlabel('Time (s)')
        ax.plot(self.times, self.values)

    def append(self, time, value):
        self.times.append(time)
        self.values.append(value)
