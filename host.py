from __future__ import division

import globals_

from device import Device
from packet import Packet


class Host(Device):
    def __init__(self, id_):
        super(Host, self).__init__(id_)

        # A list of packets that we still need to send
        self.packets_to_send = []

        # Map from packet id to packet object
        self.packets_waiting_for_acks = dict()

        # The data packets this host sends will have the ids 0, 1, 2, ...
        self.next_unused_packet_id = 0

        self.in_sending_chain = False

        # A list of flow objects whose source is this host
        self.flows = []

    def add_flow(self, flow_obj):
        self.flows.append(flow_obj)

    def receive_packet(self, packet):
        # TODO(agf): This line is temporary. Remove it when we support routing tables.
        if packet.dst != self.id_:
            return

        assert packet.dst == self.id_
        if packet.ack:
            # TODO(agf): I'm here
        # if packet.ack:
        #     globals_.event_manager.log('{} received ack for {}'.format(self.id_, packet))
        #     assert packet.id_ in self.packets_waiting_for_acks
        #     original_packet = self.packets_waiting_for_acks[packet.id_]
        #     if packet.src == original_packet.dst and packet.dst == original_packet.src:
        #         del self.packets_waiting_for_acks[packet.id_]
        else:
            # Log reception for statistics
            packet.flow.log_packet_received()
            # Create an ack packet and insert it to the front of our list of packets to send
            # So, this ack should be the next packet sent
            ack = Packet(id_=packet.id_,
                         src=self.id_,
                         dst=packet.src,
                         size=globals_.ACK_SIZE,
                         ack=True)
            # TODO(agf): Do we really want to send acks immediately?
            self.send_packet(ack)

    def send_packet(self, packet):
        self.get_endpoint_for_outgoing_packet(packet).receive_from_device(packet)
        # if not packet.ack:
        #     self.packets_waiting_for_acks[packet.id_] = packet
        #     def ack_is_due():
        #         if packet.id_ in self.packets_waiting_for_acks:
        #             globals_.event_manager.log(
        #                     '{} is due to receive an ack for {}, has not received it'.format(
        #                         self.id_, packet.id_))
        #             self.packets_to_send.insert(0, packet)
        #         else:
        #             globals_.event_manager.log(
        #                     '{} is due to receive an ack for {}, has already received it'.format(
        #                         self.id_, packet.id_))
        #     globals_.event_manager.add(globals_.TIME_TO_WAIT_UNTIL_ACK, ack_is_due)

    def act(self):
        return False
        # for flow in
        # if not self.in_sending_chain and self.packets_to_send:
        #     self.in_sending_chain = True
        #     def send_packet_and_schedule_next_send():
        #         if not self.packets_to_send:
        #             self.in_sending_chain = False
        #             return
        #         packet = self.packets_to_send.pop(0)
        #         self.send_packet(packet)
        #         globals_.event_manager.log('{} sent packet {}'.format(self.id_, packet))
        #         globals_.event_manager.add(
        #                 globals_.TIME_BETWEEN_SENDS, send_packet_and_schedule_next_send)
        #     globals_.event_manager.add(0, send_packet_and_schedule_next_send)
        #     return True
        # return False
