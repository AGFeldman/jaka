from device import Device


class Router(Device):
    def send_packet(self, packet):
        self.get_endpoint_for_outgoing_packet(packet).receive_from_device(packet)

    def receive_packet(self, packet):
        self.send_packet(packet)

    def act(self):
        return False
