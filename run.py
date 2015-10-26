import random
import sys
import json

import globals_

from event_manager import EventManager
from link import Link
from host import Host
from flow import Flow

import check_json


def get_actors_flows(description):
    '''
    Takes a string |description| of the network topology and flows.
    Parses |description| and returns (actors, flows).
    |actors| is a list of objects associated with all the pieces of equipment
    in the network. These objects should be initialized.
    |flows| is a list of elements of the form (time, setup_function).
    |time| is the time, in seconds, at which the flow starts.

    In this example code, |description| is printed and then ignored, and
    hard-coded network topology and flow are used.

    TODO(agf): Other user inputs? Run for user-specified time?
    '''
    entities = json.loads(description)
    check_json.check(entities)

    # Map from host id to host object
    hosts_and_routers = dict()

    for entity in entities:
        if entity['type'] == 'host':
            id_ = entity['id']
            hosts_and_routers[id_] = Host(id_=id_)
        if entity['type'] == 'router':
            raise 'Routers are not supported yet!'

    # Links need to be initialized after hosts and routers because Link
    # constructor takes references to hosts/routers
    links = []
    for entity in entities:
        if entity['type'] == 'link':
            links.append(Link(id_=entity['id'],
                              device1=hosts_and_routers[entity['endpoints'][0]],
                              device2=hosts_and_routers[entity['endpoints'][1]],
                              rate=entity['rate'],
                              delay=entity['delay'],
                              buffer_size=entity['buffer']))

    flows = []
    for entity in entities:
        if entity['type'] == 'flow':
            flows.append(Flow(id_=entity['id'],
                              start=entity['start'],
                              amount=entity['amount'],
                              src_obj=hosts_and_routers[entity['src']],
                              dst_obj=hosts_and_routers[entity['dst']]))

    actors = hosts_and_routers.values() + links
    return actors, flows


def simulate(description):
    '''
    Takes a string |description| of the network topology and flows.
    Runs the simulation!
    '''
    actors, flows = get_actors_flows(description)
    globals_.event_manager.set_actors(actors)
    for flow in flows:
        flow.schedule_with_event_manager()
    globals_.event_manager.run()


def main_setup():
    '''
    This should be called at the beginning of main if you're running unit tests
    or simulations.
    It seeds the random number generator and sets the global variable
    |globals_.event_manager|.
    We need to set |globals_.event_manager| for most class definitions and helper
    functions to make sense.
    '''
    random.seed(0)
    globals_.event_manager = EventManager()


if __name__ == '__main__':
    main_setup()
    simulate(sys.stdin.read())
