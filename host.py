from device import Device
from packet import AckPacket, DataPacket


class Host(Device):
    def __init__(self, id_):
        Device.__init__(self, id_)
        self.endpoint_for_router = None

    def plug_in_link(self, link_endpoint):
        assert self.endpoint_for_router is None
        self.endpoint_for_router = link_endpoint

    def receive_packet(self, packet):
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
        assert self.endpoint_for_router is not None
        self.endpoint_for_router.receive_from_device(packet)

    def act(self):
        return False
