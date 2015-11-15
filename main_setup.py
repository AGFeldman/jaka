import random

from event_manager import EventManager
from stats_manager import StatsManager
import globals_


def main_setup(output_name):
    '''
    This should be called at the beginning of main if you're running unit tests
    or simulations.
    It seeds the random number generator and sets the global variable
    |globals_.event_manager|.
    We need to set |globals_.event_manager| for most class definitions and helper
    functions to make sense.
    '''
    random.seed(0)
    globals_.event_manager = EventManager(output_name)
    globals_.stats_manager = StatsManager(output_name)
