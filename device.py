import random


class Device(object):
    '''
    Hosts, Routers, and Switches are Devices
    '''
    def __init__(self, id_):
        self.id_ = id_
        # Map from host ids to LinkEndpoints
        self.routing_table = dict()

        # TODO(agf): This line is temporary. Remove it when we support routing tables.
        self.link_endpoints = []

    def plug_in_link(self, link_endpoint):
        '''
        link_endpoint should be a LinkEndpoint
        '''
        # TODO(agf): This line is temporary. Remove it when we support routing tables.
        self.link_endpoints.append(link_endpoint)

    def get_endpoint_for_outgoing_packet(self, packet):
        if packet.dst in self.routing_table:
            return self.routing_table[packet.dst]

        # TODO(agf): This line is temporary. Remove it when we support routing tables.
        return random.choice(self.link_endpoints)

    def send_packet(self, packet):
        raise NotImplementedError

    def recieve_packet(self, packet):
        raise NotImplementedError
