import globals_

from event_manager import EventManager
from stats_manager import StatsManager, Datum

def main_setup():
    globals_.event_manager = EventManager()
    globals_.stats_manager = StatsManager()

if __name__ == '__main__':
    main_setup()
    tag = globals_.stats_manager.new_graph()
    val = 10
    time_step = 3
    def gen_data():
        '''
        Adds data to the graph at random time intervals
        '''
        print "unz"
        globals_.stats_manager.notify(Datum(tag, val))
        time = globals_.event_manager.get_time()
        if time < 100:
            globals_.event_manager.add(time_step, gen_data)
    globals_.event_manager.add(0, gen_data)
    globals_.event_manager.run()
