from __future__ import division

import globals_

from device import Device
from packet import Packet


class Host(Device):
    def receive_packet(self, packet):
        # TODO(agf): This line is temporary. Remove it when we support routing tables.
        if packet.dst != self.id_:
            return

        assert packet.dst == self.id_
        if packet.ack:
            packet.flow.receive_ack(packet)
        else:
            # Log reception for statistics
            packet.flow.log_packet_received()
            # Send an ack immediately
            # TODO(agf): Do we really want to send acks immediately?
            ack = Packet(id_=packet.id_,
                         src=self.id_,
                         dst=packet.src,
                         size=globals_.ACK_SIZE,
                         ack=True,
                         flow=packet.flow)
            self.send_packet(ack)

    def send_packet(self, packet):
        self.get_endpoint_for_outgoing_packet(packet).receive_from_device(packet)

    def act(self):
        return False
