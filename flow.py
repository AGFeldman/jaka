from __future__ import division

import globals_


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

        # Used for statistics
        # TODO(agf): This is likely to be a very long list (and we even know
        # what the length will be!), so performance might be improved
        # significantly by making this an array or something
        self.times_packets_were_received = []

    def generate_packets_to_send(self):
        npackets = self.amount // globals_.DATA_PACKET_SIZE
        if self.amount % globals_.DATA_PACKET_SIZE != 0:
            npackets += 1
        for _ in xrange(npackets):
            self.src_obj.generate_packet(self.dst_obj.id_, self)

    def schedule_with_event_manager(self):
        def setup_flow():
            self.generate_packets_to_send()
        globals_.event_manager.add(self.start, setup_flow)

    def log_packet_received(self):
        self.times_packets_were_received.append(globals_.event_manager.get_time())
