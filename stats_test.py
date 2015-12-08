import random

import globals_

from event_manager import EventManager
from stats_manager import StatsManager


def main_setup():
    random.seed(0)
    globals_.event_manager = EventManager(None)
    globals_.stats_manager = StatsManager('output')

if __name__ == '__main__':
    global val
    main_setup()
    tag_a = globals_.stats_manager.new_graph(
        title='Random walk',
        ylabel='Walk value',
        dataset_label='Walk A',
        graph_id='walks'
    )
    tag_b = globals_.stats_manager.new_graph(
        # There can be duplicates of title, ylabel, etc. here
        graph_id='walks',
        dataset_label='Walk B'
    )
    # hack to allow modifying outer variable
    # from within a closure
    val_a = [10]
    val_b = [10]
    time_step = 0.1
    def gen_data():
        '''
        Adds data to the graph at random time intervals
        '''
        globals_.stats_manager.notify(tag_a, val_a[0])
        globals_.stats_manager.notify(tag_b, val_b[0])
        val_a[0] += random.randint(-1, 1)
        val_b[0] += random.randint(-1, 1)
        time = globals_.event_manager.get_time()
        if time < 100:
            globals_.event_manager.add(time_step, gen_data)
    globals_.event_manager.add(0, gen_data)
    globals_.event_manager.run()
    globals_.stats_manager.output_graphs()
