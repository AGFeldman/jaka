import random

import globals_

from event_manager import EventManager
from stats_manager import StatsManager, Datum


def main_setup():
    random.seed(0)
    globals_.event_manager = EventManager()
    globals_.stats_manager = StatsManager()

if __name__ == '__main__':
    global val
    main_setup()
    tag = globals_.stats_manager.new_graph(
        title='Random walk',
        ylabel='Walk value'
    )
    # hack to allow modifying outer variable
    # from within a closure
    val = [10]
    time_step = 3
    def gen_data():
        '''
        Adds data to the graph at random time intervals
        '''
        globals_.stats_manager.notify(Datum(tag, val[0]))
        val[0] += random.randint(-1,1)
        time = globals_.event_manager.get_time()
        if time < 100:
            globals_.event_manager.add(time_step, gen_data)
    globals_.event_manager.add(0, gen_data)
    globals_.event_manager.run()
    globals_.stats_manager.output_graphs()
