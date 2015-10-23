import random
import sys
import json

import globals_

from event_manager import EventManager
from packet import Packet
from link import Link, LinkEndpoint
from host import Host

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

    def is_host(entity):
        return entity['id'][0] in 'HST'
    def is_link(entity):
        return entity['id'][0] == 'L'
    def is_router(entity):
        return entity['id'][0] == 'R'
    def is_flow(entity):
        return entity['id'][0] == 'F'

    # Map from host id to host object
    hosts_and_routers = dict()

    for entity in entities:
        if is_host(entity):
            id_ = entity['id']
            hosts_and_routers[id_] = Host(id_=id_)
        if is_router(entity):
            raise 'Routers are not supported yet!'

    # Links need to be initialized after hosts and routers because Link
    # constructor takes references to hosts/routers
    links = []
    for entity in entities:
        if is_link(entity):
            links.append(Link(id_=entity['id'],
                              device1=hosts_and_routers[entity['endpoints'][0]],
                              device2=hosts_and_routers[entity['endpoints'][1]],
                              rate=entity['rate'],
                              delay=entity['delay'],
                              buffer_size=entity['buffer']))

    flows = []
    for entity in entities:
        if is_flow(entity):
            # TODO(agf): Assert that src and dst are hosts
            def setup_flow():
                hosts_and_routers[entity['src']].generate_packets_to_send(
                        entity['dst'], entity['amount'])
            flows.append((entity['start'], setup_flow))

    actors = hosts_and_routers.values() + links
    return actors, flows


def simulate(description):
    '''
    Takes a string |description| of the network topology and flows.
    Runs the simulation!
    '''
    actors, flows = get_actors_flows(description)
    globals_.event_manager.set_actors(actors)
    for start_time, setup_flow in flows:
        globals_.event_manager.add(start_time, setup_flow)
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
