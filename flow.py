from __future__ import division

import globals_

from packet import Packet


class RTTE(object):
    '''
    Keep a Round Trip Time estimate
    Public members:
        self.estimate
    '''
    def __init__(self):
        # Initial estimate is 100 ms
        self.estimate = 0.1
        # TODO(agf): Finish implementing


class Flow(object):
    def __init__(self, id_=None, start=None, amount=None, src_obj=None, dst_obj=None):
        '''
        id_ is e.g. "F1"
        start is the time that the flow should start, in seconds
        amount is the amount of data to send, in bits
        src_obj is the Host object for the source
        dst_obj is the Host object for the destination
        '''
        self.id_ = id_
        self.start = start
        self.amount = amount
        self.src_obj = src_obj
        self.dst_obj = dst_obj

        self.src_obj.add_flow(self)

        self.packets = []
        self._generate_packets_to_send()

        # Used for statistics
        # TODO(agf): This is likely to be a very long list (and we even know
        # what the length will be!), so performance might be improved
        # significantly by making this an array or something
        self.times_packets_were_received = []

    def receive_ack(packet_id):
        # TODO(agf): Implement

    def start_sending():
        # TODO(agf): Implement
        pass

    def _generate_packets_to_send(self):
        '''
        Fill self.packets with the packets that we want to send
        '''
        npackets = self.amount // globals_.DATA_PACKET_SIZE
        if self.amount % globals_.DATA_PACKET_SIZE != 0:
            npackets += 1
        for id_ in xrange(npackets):
            self.packets.append(Packet(id_=id_,
                                       src=self.src_obj.id_,
                                       dst=self.dst_obj.id_,
                                       size=globals_.DATA_PACKET_SIZE,
                                       ack=False,
                                       flow=self))

    def schedule_with_event_manager(self):
        def setup():
            self.start_sending()
        globals_.event_manager.add(self.start, setup)

    def log_packet_received(self):
        self.times_packets_were_received.append(globals_.event_manager.get_time())
