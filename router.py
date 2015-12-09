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
            self.routing_table[link_endpoint.distant_device.id_] = (
                    link_endpoint, link_endpoint.link.get_cost())
            # Shallow copy
            self.provisional_routing_table = copy.copy(self.routing_table)
            self.endpoints_to_hosts.append(link_endpoint)
            return
        assert isinstance(link_endpoint.distant_device, Router)
        # Assume that any two devices have at most one direct link between them
        self.endpoints_to_routers[link_endpoint.distant_device.id_] = link_endpoint

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
        if not isinstance(packet, RoutingPacket):
            self.send_packet(packet)
            return

        # Handle routing packets
        # In order to converge eventually, it is sufficient to:
        # - Start by having all routers send routing packets to all their neighbors
        # - If a router updates its table, then it should send routing packets to all its neighbors
        # However, this will not give us a way to know *when* we have converged.
        # We don't even try to guess when convergence has occurred. We just establish beats.
        # See initialize_routing_packets_beat() and initialize_routing_tables_beat().

        updated_table = False

        endpoint_to_other_router = self.endpoints_to_routers[packet.src]
        dist_to_other_router = endpoint_to_other_router.link.get_cost()

        for dst_id, dist in packet.distances:
            alt_cost = dist_to_other_router + dist
            if dst_id not in self.provisional_routing_table:
                self.provisional_routing_table[dst_id] = (endpoint_to_other_router, alt_cost)
                updated_table = True
            else:
                cur_forwarding_endpoint, current_cost = self.provisional_routing_table[dst_id]
                if alt_cost < current_cost:
                    self.provisional_routing_table[dst_id] = (endpoint_to_other_router, alt_cost)
                    updated_table = True
                elif cur_forwarding_endpoint is endpoint_to_other_router and (
                        alt_cost > current_cost):
                    self.provisional_routing_table[dst_id] = (endpoint_to_other_router,
                                                              float('inf'))
                    updated_table = True

        # Cost to send directly to an adjacent host might also have changed
        for endpoint in self.endpoints_to_hosts:
            dst_id = endpoint.distant_device.id_
            direct_cost = endpoint.link.get_cost()
            cur_forwarding_endpoint, current_cost = self.provisional_routing_table[dst_id]
            if direct_cost < current_cost:
                self.provisional_routing_table[dst_id] = (endpoint, direct_cost)
                updated_table = True
            elif endpoint is cur_forwarding_endpoint and direct_cost > current_cost:
                self.provisional_routing_table[dst_id] = (endpoint, float('inf'))
                updated_table = True

        if updated_table:
            self.send_routing_packets()

    def send_routing_packets(self):
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
        Links measure their cost to this beat
        '''
        def one_off_send():
            self.send_routing_packets()
        globals_.event_manager.add(0, one_off_send)
        def beat():
            for endpoint in self.endpoints_to_hosts + self.endpoints_to_routers.values():
                endpoint.link.measure_cost()
            self.send_routing_packets()
            globals_.event_manager.add(globals_.SEND_ROUTING_PACKETS_EVERY, beat)
        globals_.event_manager.add(0.05, beat)

    def log_routing_table(self):
        globals_.event_manager.log('Routing table for {} is {}'.format(self, self.routing_table))

    def switch_routing_table(self):
        self.routing_table = copy.copy(self.provisional_routing_table)
        self.log_routing_table()
        for endpoint in self.endpoints_to_hosts + self.endpoints_to_routers.values():
            endpoint.link.reset_cost()

    def initialize_routing_tables_beat(self):
        def beat():
            self.switch_routing_table()
            globals_.event_manager.add(globals_.SWITCH_ROUTING_TABLE_EVERY, beat)
        globals_.event_manager.add(globals_.INITIAL_ROUTING_TABLE_SWITCH, beat)

    def register_with_event_manager(self):
        self.initialize_routing_packets_beat()
        self.initialize_routing_tables_beat()

    def act(self):
        return False
