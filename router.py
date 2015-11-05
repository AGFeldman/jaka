from device import Device

import globals_


class Router(Device):
    def __init__(self, id_):
        Device.__init__(self, id_)
        # Map from host ids to LinkEndpoints
        self.routing_table = dict()
        # TODO(agf): I'm not sure if we we want to do anything with
        # self.link_endpoints, but it seems useful
        self.link_endpoints = []

    def plug_in_link(self, link_endpoint):
        # TODO(agf): What if there are multiple direct links to the same destination?
        self.routing_table[link_endpoint.distant_device.id_] = link_endpoint
        # TODO(agf): This might not be needed, but seems useful
        self.link_endpoints.append(link_endpoint)

    def send_packet(self, packet):
        if packet.dst not in self.routing_table:
            globals_.event_manager.log('{} could not determine where to send {}'.format(
                self, packet))
            return
        self.routing_table[packet.dst].receive_from_device(packet)

    def receive_packet(self, packet):
        self.send_packet(packet)

    def act(self):
        return False
