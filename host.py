import globals_

from device import Device
from packet import Packet


ACK_SIZE = 15  # or something
DATA_PACKET_SIZE = 1500  # or something

# These are heavy-handed simplifications
TIME_BETWEEN_SENDS = 1
TIME_TO_WAIT_UNTIL_ACK = 10
PORT = 0


class Host(Device):
    def __init__(self, id_=None):
        super(Host, self).__init__(id_=id_)
        # maybe it should have a list of packets to send, a list of packets
        # recieved and not processed yet, and a set of packets sent and still
        # waiting for acks
        self.packets_to_send = []
        # map from packet id to packet
        # TODO(agf): This relies on packet ids being unique over all the
        # packets sent by any one host
        self.packets_waiting_for_acks = dict()
        self.next_unused_packet_id = 0
        self.in_sending_chain = False

    def generate_packet(self, dst_id):
        self.packets_to_send.append(Packet(id_=self.next_unused_packet_id, src=self.id_, dst=dst_id, size=DATA_PACKET_SIZE, ack=False))
        self.next_unused_packet_id += 1

    def generate_packets_to_send(self, dst_id, how_much_data):
        npackets = how_much_data // DATA_PACKET_SIZE
        if how_much_data % DATA_PACKET_SIZE != 0:
            npackets += 1
        for _ in xrange(npackets):
            self.generate_packet(dst_id)

    def receive_packet(self, packet):
        assert packet.dst == self.id_
        if packet.ack:
            globals_.event_manager.log('{} received ack for {}'.format(self.id_, packet))
            assert packet.id_ in self.packets_waiting_for_acks
            original_packet = self.packets_waiting_for_acks[packet.id_]
            if packet.src == original_packet.dst and packet.dst == original_packet.src:
                del self.packets_waiting_for_acks[packet.id_]
        else:
            # Send an ack
            ack = Packet(id_=packet.id_, src=self.id_, dst=packet.src, size=ACK_SIZE, ack=True)
            # Schedule the ack to be the next packet sent
            self.packets_to_send.insert(0, ack)

    def send_packet(self, packet, port):
        self.ports[port].receive_from_device(packet)
        if not packet.ack:
            self.packets_waiting_for_acks[packet.id_] = packet
            def ack_is_due():
                if packet.id_ in self.packets_waiting_for_acks:
                    globals_.event_manager.log('{} is due to receive an ack for {}, has not received it'.format(self.id_, packet.id_))
                    self.packets_to_send.insert(0, packet)
                else:
                    globals_.event_manager.log('{} is due to receive an ack for {}, has already received it'.format(self.id_, packet.id_))
            description = '{} is due to receive an ack for {}'.format(self.id_, packet.id_)
            globals_.event_manager.add(TIME_TO_WAIT_UNTIL_ACK, ack_is_due)

    def act(self):
        if not self.in_sending_chain and self.packets_to_send:
            self.in_sending_chain = True
            def send_packet_and_schedule_next_send():
                if not self.packets_to_send:
                    self.in_sending_chain = False
                    return
                packet = self.packets_to_send.pop(0)
                self.send_packet(packet, PORT)
                globals_.event_manager.log('{} sent packet {} on port {}'.format(self.id_, packet, PORT))
                globals_.event_manager.add(TIME_BETWEEN_SENDS, send_packet_and_schedule_next_send)
            globals_.event_manager.add(0, send_packet_and_schedule_next_send)
            return True
        return False
