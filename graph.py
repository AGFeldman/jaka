from __future__ import division

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import globals_


class Graph(object):
    '''
    Stores all the information about a graph.
    '''

    def __init__(self,
                 title=None,
                 ylabel=None,
                 is_rate=False,
                 sliding_window_width=globals_.DEFAULT_GRAPH_SLIDING_WINDOW_WIDTH,
                 sliding_window_step=globals_.DEFAULT_GRAPH_SLIDING_WINDOW_STEP):
        '''
        If is_rate is True, then the data is plotted as a rate.
            Rate data points are |sliding_window_step| seconds apart.
            Rate data points consider the last |sliding_window_width| seconds of
            values when computing rate.
        '''
        self.title = title
        self.ylabel = ylabel
        self.is_rate = is_rate
        self.sliding_window_width = sliding_window_width
        self.sliding_window_step = sliding_window_step
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
        if self.is_rate:
            if not self.times:
                return
            rate_times, rate_values = self.get_rate_data()
            ax.plot(rate_times, rate_values)
        else:
            ax.plot(self.times, self.values)

    def get_rate_data(self):
        beginning_of_sliding_window_index = 0
        end_of_sliding_window_index = 0
        rate_times = []
        rate_values = []
        end_of_window = self.sliding_window_step
        while end_of_window < self.times[-1]:
            while (self.times[beginning_of_sliding_window_index] <
                   end_of_window - self.sliding_window_width):
                beginning_of_sliding_window_index += 1
                if beginning_of_sliding_window_index > len(self.times):
                    break
            if beginning_of_sliding_window_index > len(self.times):
                break
            while self.times[end_of_sliding_window_index] < end_of_window:
                end_of_sliding_window_index += 1
                if end_of_sliding_window_index > len(self.times):
                    break
            if end_of_sliding_window_index <= beginning_of_sliding_window_index:
                rate_times.append(end_of_window)
                rate_values.append(0)
                end_of_window += self.sliding_window_step
                continue
            sum_ = 0
            count = 0
            for index in xrange(beginning_of_sliding_window_index, end_of_sliding_window_index):
                sum_ += self.values[index]
                count += 1
            rate_times.append(end_of_window)
            # Change in value
            dvalue = (self.values[end_of_sliding_window_index] -
                      self.values[beginning_of_sliding_window_index])
            # Change in time
            dtime = (self.times[end_of_sliding_window_index] -
                     self.times[beginning_of_sliding_window_index])
            rate_values.append(dvalue / dtime)
            end_of_window += self.sliding_window_step
        return rate_times, rate_values

    def append(self, time, value):
        self.times.append(time)
        self.values.append(value)
