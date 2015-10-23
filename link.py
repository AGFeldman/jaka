import globals_


class LinkEndpoint(object):
    def __init__(self, device=None, buffer_size=0):
        '''
        buffer_size is in bytes
        buffer_space_free is in bytes
        '''
        self.device = device
        self.buffer_size = buffer_size
        self.buffer_space_free = self.buffer_size
        # buffer elements should be (packet, time_packet_was_added)
        # buffer should always be sorted from least recently added to most recently added
        self.buffer = []

    def receive_from_device(self, packet):
        # TODO(agf): Add fields 'stats_packets_received' and 'stats_packets_dropped'
        if self.buffer_space_free >= packet.size:
            self.buffer.append((packet, globals_.event_manager.get_time()))
            self.buffer_space_free -= packet.size
        else:
            globals_.event_manager.log('endpoint associated with {} dropped {}'.format(self.device.id_, packet))

    def peek_lra(self):
        '''
        lra stands for 'least recently added'
        returns (packet, time_packet_was_added) for the least recently added packet
        '''
        if self.buffer:
            return self.buffer[0]

    def dequeue_lra(self):
        '''
        lra stands for 'least recently added'
        returns pops (packet, time_packet_was_added) from buffer and returns packet
        assumes that self.buffer is not empty
        '''
        packet = self.buffer.pop(0)[0]
        self.buffer_space_free += packet.size
        return packet


class Link(object):
    def __init__(self, id_=None, device1=None, device2=None, rate=0, delay=0, buffer_size=0):
        '''
        device1 and device2 should be Host, Router, or Switch objects
        rate is in bytes per second
        delay is in seconds
        buffer_size is in bytes
        self.state is either 'sending' or 'not_sending'
        '''
        self.id_ = id_
        self.rate = rate
        self.delay = delay

        self.endpoint1 = LinkEndpoint(device=device1, buffer_size=buffer_size)
        self.endpoint2 = LinkEndpoint(device=device2, buffer_size=buffer_size)
        device1.plug_in_link(self.endpoint1)
        device2.plug_in_link(self.endpoint2)

        self.packet_on_link = None

    def transit_time(self, packet):
        return packet.size / self.rate + self.delay

    def get_src_dst_endpoints(self):
        '''
        Used to determine if we can load another packet onto the link, and, if
        so, which direction the packet should travel
        '''
        if not self.endpoint1.buffer and not self.endpoint2.buffer:
            return
        if self.endpoint1.buffer and not self.endpoint2.buffer:
            return self.endpoint1, self.endpoint2
        if not self.endpoint1.buffer and self.endpoint2.buffer:
            return self.endpoint2, self.endpoint1
        lra1_time = self.endpoint1.peek_lra()[1]
        lra2_time = self.endpoint2.peek_lra()[1]
        if lra1_time < lra2_time:
            return self.endpoint1, self.endpoint2
        if lra1_time > lra2_time:
            return self.endpoint2, self.endpoint1
        return random.choice(((self.endpoint1, self.endpoint2),
                              (self.endpoint2, self.endpoint1)))

    def send(self, src_endpoint, dst_endpoint):
        # TODO(agf): We should have one event for "finished loading packet into
        # link" and another event, self.delay seconds later, for "finished
        # delivering packet". In this way, multiple packets can exist in the
        # link at one time. So, we should change self.packet_on_link to
        # self.loading_packet_into_link. But, does this run into any issues
        # with the link being half-duplex?
        assert not self.packet_on_link
        self.packet_on_link = src_endpoint.dequeue_lra()
        def packet_reaches_endpoint():
            globals_.event_manager.log('{} delivered {} to the endpoint associated with {}'.format(self.id_, self.packet_on_link, dst_endpoint.device.id_))
            dst_endpoint.device.receive_packet(self.packet_on_link)
            self.packet_on_link = None
        globals_.event_manager.add(self.transit_time(self.packet_on_link), packet_reaches_endpoint)

    def act(self):
        if self.packet_on_link:
            return
        src_dst_endpoints = self.get_src_dst_endpoints()
        if src_dst_endpoints:
            self.send(*src_dst_endpoints)
