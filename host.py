from __future__ import division

import globals_

from device import Device
from packet import AckPacket, DataPacket


class Host(Device):
    def receive_packet(self, packet):
        # TODO(agf): This line is temporary. Remove it when we support routing tables.
        if packet.dst != self.id_:
            return

        assert packet.dst == self.id_
        if isinstance(packet, AckPacket):
            packet.flow.receive_ack(packet)
        else:
            assert isinstance(packet, DataPacket)
            # Log reception for statistics
            packet.flow.log_packet_received()
            # Send an ack immediately
            # TODO(agf): Do we really want to send acks immediately?
            ack = AckPacket(id_=packet.id_,
                            src=self.id_,
                            dst=packet.src,
                            flow=packet.flow)
            self.send_packet(ack)

    def send_packet(self, packet):
        self.get_endpoint_for_outgoing_packet(packet).receive_from_device(packet)

    def act(self):
        return False
