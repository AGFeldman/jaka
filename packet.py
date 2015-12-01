import globals_


class Packet(object):
    def __init__(self, id_=None, src=None, dst=None, flow=None, size=None):
        '''
        id_ is used for both data packet and corresponding ack packet. This could change.
        src is source_host.id_
        dst is destination_host.id_
        size is packet size in bits
        ack is True iff this packet is an acknowledgement
        '''
        assert id_ is not None
        assert src is not None
        assert dst is not None
        assert size is not None
        assert flow is not None
        self.id_ = id_
        self.src = src
        self.dst = dst
        self.size = size
        self.flow = flow

    def __str__(self):
        return '({}, id={}, src={}, dst={})'.format(type(self), self.id_, self.src, self.dst)


class DataPacket(Packet):
    def __init__(self, id_=None, src=None, dst=None, flow=None, timeout=None):
        Packet.__init__(self, id_=id_, src=src, dst=dst, flow=flow, size=globals_.DATA_PACKET_SIZE)
        self.timeout = timeout


class AckPacket(Packet):
    def __init__(self, id_=None, src=None, dst=None, flow=None, next_expected=None):
        Packet.__init__(self, id_=id_, src=src, dst=dst, flow=flow, size=globals_.ACK_SIZE)

        # Next packet sequence number (ie id_) expected by the receiving end of a flow
        self.next_expected = next_expected

    def __str__(self):
        return '({}, id={}, src={}, dst={}, nxt={})'.format(type(self), self.id_, self.src, self.dst, self.next_expected)

class RoutingPacket(Packet):
    def __init__(self, src=None, distances=None):
        '''
        distances is a list of (destination_id, estimated_distance_to_destination) tuples
        '''
        assert src is not None
        assert distances is not None
        self.id_ = 'TODO(agf): Routing packets don\'t have ids'
        self.src = src
        self.distances = distances
        self.size = globals_.DATA_PACKET_SIZE

    def __str__(self):
        return '(routing packet from {})'.format(self.id_)
