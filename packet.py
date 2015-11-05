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
    def __init__(self, id_=None, src=None, dst=None, flow=None):
        Packet.__init__(self, id_=id_, src=src, dst=dst, flow=flow, size=globals_.DATA_PACKET_SIZE)


class AckPacket(Packet):
    def __init__(self, id_=None, src=None, dst=None, flow=None):
        Packet.__init__(self, id_=id_, src=src, dst=dst, flow=flow, size=globals_.ACK_SIZE)


class RoutingPacket(Packet):
    def __init__(self, id_=None, src=None, dst=None, flow=None, distances=None):
        '''
        distances is a dictionary that maps dst_id -> distance_estimate
        '''
        Packet.__init__(self, id_=id_, src=src, dst=dst, flow=flow, size=globals_.DATA_PACKET_SIZE)
        assert distances is not None
        self.distances = distances
