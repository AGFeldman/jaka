import copy

from device import Device
from host import Host
from packet import RoutingPacket

import globals_


class Router(Device):
    def __init__(self, id_):
        Device.__init__(self, id_)
        # Map: host_id -> (LinkEndpoint,
        #                  estimated_cost_to_get_to_host_id_by_going_through_this_link_endpoint)
        self.routing_table = dict()
        self.provisional_routing_table = dict()

        # List of link endpoints whose links connect directly to hosts
        self.endpoints_to_hosts = []

        # Map: router_id -> endpoint of a link that connects to that router
        self.endpoints_to_routers = dict()

    def plug_in_link(self, link_endpoint):
        if isinstance(link_endpoint.distant_device, Host):
            self.routing_table[link_endpoint.distant_device.id_] = (link_endpoint,
                                                                    link_endpoint.get_cost())
            # Shallow copy
            self.provisional_routing_table = copy.copy(self.routing_table)
            self.endpoints_to_hosts.append(link_endpoint)
            return
        assert isinstance(link_endpoint.distant_device, Router)
        self.endpoints_to_routers[link_endpoint.distant_device.id_] = link_endpoint
        # TODO(agf): What if there are multiple direct links to the same destination?

    def send_packet(self, packet):
        '''
        Send a data packet or an ack
        Use send_routing_packets() to send routing packets
        '''
        if packet.dst not in self.routing_table:
            globals_.event_manager.log('{} could not determine where to send {}'.format(
                self, packet))
            return
        self.routing_table[packet.dst][0].receive_from_device(packet)

    def receive_packet(self, packet):
        globals_.event_manager.log('{} received some packet')

        if not isinstance(packet, RoutingPacket):
            self.send_packet(packet)
            return

        globals_.event_manager.log('{} received routing packet {}'.format(self, packet))

        # Handle routing packets
        # In order to converge eventually, it is sufficient to:
        # - Start by having all routers send routing packets to all their neighbors
        # - If a router updates its table, then it should send routing packets to all its neighbors
        # However, this will not give us a way to know *when* we have converged.
        # We don't even try to guess when convergence has occurred. We just establish beats.
        # See initialize_routing_packets_beat() and initialize_routing_tables_beat().

        updated_table = False

        endpoint_to_other_router = self.endpoints_to_routers[packet.src]
        dist_to_other_router = endpoint_to_other_router.get_cost()

        for dst_id, dist in packet.distances:
            alt_cost = dist_to_other_router + dist
            if dst_id not in self.provisional_routing_table:
                self.provisional_routing_table[dst_id] = (endpoint_to_other_router, alt_cost)
                updated_table = True
            else:
                _, current_cost = self.provisional_routing_table[dst_id]
                if alt_cost < current_cost:
                    self.provisional_routing_table[dst_id] = (endpoint_to_other_router, alt_cost)
                    updated_table = True

        # Cost to send directly to an adjacent host might also have changed
        for endpoint in self.endpoints_to_hosts:
            dst_id = endpoint.distant_device.id_
            direct_cost = endpoint.get_cost()
            _, current_cost = self.provisional_routing_table[dst_id]
            if direct_cost < current_cost:
                self.provisional_routing_table[dst_id] = (endpoint, direct_cost)
                updated_table = True

        if updated_table:
            self.send_routing_packets()
        # TODO(agf): What if routing packets get dropped?
        # Should we get acks for routing packets?
        # Can routers do anything to make sure that they don't overflow the
        # buffers? (Can we think of the buffers as "inside" the routers?) (No)

    def send_routing_packets(self):
        globals_.event_manager.log('{} call to send_routing_packets'.format(self))
        distances = []
        for host_id in self.provisional_routing_table:
            _, dist = self.provisional_routing_table[host_id]
            distances.append((host_id, dist))
        packet = RoutingPacket(src=self.id_, distances=distances)
        for router_endpoint in self.endpoints_to_routers.values():
            router_endpoint.receive_from_device(packet)
            globals_.event_manager.log('{} sent routing packet to {}'.format(
                self, router_endpoint.device.id_))

    def initialize_routing_packets_beat(self):
        '''
        Schedule send_routing_packets() to be called immediately
        And, schedule send_routing_packets() to be called in 50 ms, in case
        routing packets have been dropped
        Schedule send_routing_packets() to be called every 200 ms thereafter
        '''
        def one_off_send():
            self.send_routing_packets()
        globals_.event_manager.add(0, one_off_send)
        def beat():
            self.send_routing_packets()
            globals_.event_manager.add(0.2, beat)
        globals_.event_manager.add(0.05, beat)

    def initialize_routing_tables_beat(self):
        def beat():
            self.routing_table = copy.copy(self.provisional_routing_table)
            globals_.event_manager.add(5, beat)
        # TODO(agf): Think about when we want to set up this beat
        globals_.event_manager.add(0.4, beat)

    def register_with_event_manager(self):
        print 'i register'
        self.initialize_routing_packets_beat()
        self.initialize_routing_tables_beat()

    def act(self):
        return False
