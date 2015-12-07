from device import Device
from packet import AckPacket, DataPacket
import globals_


class Host(Device):
    def __init__(self, id_):
        Device.__init__(self, id_)
        self.endpoint_for_router = None

        self.bits_sent_graph_tag = globals_.stats_manager.new_graph(
                title='Total Bits Sent by %s' % self.id_,
                ylabel='Total Bits'
        )
        self.bit_rate_sent_graph_tag = globals_.stats_manager.new_graph(
                title='Rate of Data Sent by %s' % self.id_,
                ylabel='Rate (bits/sec)',
                is_rate=True
        )
        self.bits_received_graph_tag = globals_.stats_manager.new_graph(
                title='Total Bits Received by %s' % self.id_,
                ylabel='Total Bits'
        )
        self.bit_rate_received_graph_tag = globals_.stats_manager.new_graph(
                title='Rate of Data Received by %s' % self.id_,
                ylabel='Rate (bits/sec)',
                is_rate=True
        )

        self.bits_sent = 0
        self.bits_received = 0

    def plug_in_link(self, link_endpoint):
        assert self.endpoint_for_router is None
        self.endpoint_for_router = link_endpoint

    def receive_packet(self, packet):
        assert packet.dst == self.id_
        self.bits_received += packet.size
        globals_.stats_manager.notify(self.bits_received_graph_tag, self.bits_received)
        globals_.stats_manager.notify(self.bit_rate_received_graph_tag, self.bits_received)
        if isinstance(packet, AckPacket):
            packet.flow.receive_ack(packet)
        else:
            assert isinstance(packet, DataPacket)
            # Log reception for statistics
            # TODO(jg): combine these two into flow.receive_packet() or something
            packet.flow.log_packet_received()

            prev_next_expected = packet.flow.next_expected

            packet.flow.update_next_expected(packet.id_)
            # Send an ack immediately
            # TODO(agf): Do we really want to send acks immediately?

            if packet.id_ < prev_next_expected:
                return

            ack = AckPacket(id_=packet.id_,
                            src=self.id_,
                            dst=packet.src,
                            flow=packet.flow,
                            next_expected=packet.flow.next_expected)
            self.send_packet(ack)

    def send_packet(self, packet):
        assert self.endpoint_for_router is not None
        assert isinstance(packet, DataPacket) or isinstance(packet, AckPacket)
        self.bits_sent += packet.size
        globals_.stats_manager.notify(self.bits_sent_graph_tag, self.bits_sent)
        globals_.stats_manager.notify(self.bit_rate_sent_graph_tag, self.bits_sent)
        self.endpoint_for_router.receive_from_device(packet)

    def act(self):
        return False
