class Packet(object):
    def __init__(self, id_=None, src=None, dst=None, size=0, ack=False):
        '''
        id_ is used for both data packet and corresponding ack packet. This could change.
        src is source_host.id_
        dst is destination_host.id_
        size is packet size in bytes
        ack is True iff this packet is an acknowledgement
        '''
        self.id_ = id_
        self.src = src
        self.dst = dst
        self.size = size
        self.ack = ack

    def __str__(self):
        if self.ack:
            return '({}, {}, {}, ack)'.format(self.id_, self.src, self.dst)
        return '({}, {}, {})'.format(self.id_, self.src, self.dst)
