from __future__ import division

import globals_


class LinkEndpoint(object):
    def __init__(self, device=None, distant_device=None, buffer_size=0, link=None):
        '''
        buffer_size is in bits
        buffer_space_free is in bits
        public members:
            self.distant_device: This is Device object known to be at the other
            end of the link. This is only intended to be used to allow devices
            to know the ids and types of their neighbors.
        '''
        self.device = device
        self.distant_device = distant_device
        self.buffer_size = buffer_size
        self.buffer_space_free = self.buffer_size
        self.link = link
        # buffer elements should be (packet, time_packet_was_added)
        # buffer should always be sorted from least recently added to most recently added
        self.buffer = []

        self.packets_dropped_graph_tag = globals_.stats_manager.new_graph(
                title='Number of Packets Dropped on {}/{} endpoint'.format(
                    self.link.id_, self.device.id_),
                ylabel='Number of Packets Dropped')
        self.buffer_occupancy_graph_tag = globals_.stats_manager.new_graph(
                title='Buffer Occupancy for {}/{} endpoint'.format(
                    self.link.id_, self.device.id_),
                ylabel='Buffer Occupancy (bits)')

        self.num_packets_dropped = 0

    def __str__(self):
        return str(self.device) + '/' + str(self.link)

    def __repr__(self):
        return self.__str__()

    def get_buffer_occupancy(self):
        return self.buffer_size - self.buffer_space_free

    def get_buffer_occupancy_percentage(self):
        return self.get_buffer_occupancy() / self.buffer_size

    def notify_buffer_occupancy(self):
        globals_.stats_manager.notify(self.buffer_occupancy_graph_tag,
                                      self.get_buffer_occupancy())

    def receive_from_device(self, packet):
        if self.buffer_space_free >= packet.size:
            self.buffer.append((packet, globals_.event_manager.get_time()))
            self.buffer_space_free -= packet.size
            self.notify_buffer_occupancy()
        else:
            globals_.event_manager.log('endpoint associated with {} dropped {}'.format(
                self.device.id_, packet))
            self.num_packets_dropped += 1
            globals_.stats_manager.notify(self.packets_dropped_graph_tag,
                                          self.num_packets_dropped)

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
        self.notify_buffer_occupancy()
        return packet


class Link(object):
    def __init__(self, id_=None, device1=None, device2=None, rate=0, delay=0, buffer_size=0):
        '''
        device1 and device2 should be Host, Router, or Switch objects
        rate is in bits per second
        delay is in seconds
        buffer_size is in bits
        self.state is either 'sending' or 'not_sending'
        '''
        self.id_ = id_
        self.rate = rate
        self.delay = delay

        # A list of (time_of_measurement, cost_measurement) tuples
        self.cost_measurements = []

        self.data_sent_graph_tag = globals_.stats_manager.new_graph(
                title='Total Bits Sent Over Links',
                ylabel='Bits',
                graph_id='link_total_bits_sent_over',
                dataset_label=self.id_
        )
        self.rate_data_sent_graph_tag = globals_.stats_manager.new_graph(
                title='Rate of Sending Data Over Links',
                ylabel='Rate (bits/second)',
                is_rate=True,
                graph_id='link_rate_of_sending_data_over',
                dataset_label=self.id_
        )
        self.total_data_sent = 0

        self.endpoint1 = LinkEndpoint(device=device1,
                                      distant_device=device2,
                                      buffer_size=buffer_size,
                                      link=self)
        self.endpoint2 = LinkEndpoint(device=device2,
                                      distant_device=device1,
                                      buffer_size=buffer_size,
                                      link=self)
        device1.plug_in_link(self.endpoint1)
        device2.plug_in_link(self.endpoint2)

        self.max_bits_sent_in_sequence = globals_.LINK_MAX_BITS_IN_SEQUENCE
        self.bits_sent_in_sequence = 0
        self.packet_transmitting = None
        self.waiting_prop_time = False
        self.waiting_to_decide_direction = True
        self.src_dst_endpoints = None

        # Keep track of whether the last send direction was endpoint 1 ->
        # endpoint 2, or the other way around. Use this to break ties when
        # deciding which direction to send packets.  Pretend that before we
        # started, the last send direction was 1 to 2.
        self.last_send_dir_was_1_to_2 = True

    def __str__(self):
        return self.id_

    def return_12(self):
        '''
        Helper function for get_src_dst_endpoints()
        '''
        self.last_send_dir_was_1_to_2 = True
        return self.endpoint1, self.endpoint2

    def return_21(self):
        '''
        Helper function for get_src_dst_endpoints()
        '''
        self.last_send_dir_was_1_to_2 = False
        return self.endpoint2, self.endpoint1

    def get_src_dst_endpoints(self):
        '''
        Used to determine what direction a packet should travel if we're
        otherwise undecided
        '''
        if not self.endpoint1.buffer and not self.endpoint2.buffer:
            return
        if self.endpoint1.buffer and not self.endpoint2.buffer:
            return self.return_12()
        if not self.endpoint1.buffer and self.endpoint2.buffer:
            return self.return_21()
        lra1_time = self.endpoint1.peek_lra()[1]
        lra2_time = self.endpoint2.peek_lra()[1]
        if lra1_time < lra2_time:
            return self.return_12()
        if lra1_time > lra2_time:
            return self.return_21()
        if self.last_send_dir_was_1_to_2:
            return self.return_21()
        return self.return_12()

    def send(self, src_endpoint, dst_endpoint):
        assert self.packet_transmitting is None
        self.packet_transmitting = src_endpoint.dequeue_lra()
        def packet_finishes_transmitting():
            packet = self.packet_transmitting
            self.packet_transmitting = None
            globals_.event_manager.log(
                    '{} finished transmitting {} from endpoint associated with {}'.format(
                        self.id_, packet, src_endpoint.device.id_))
            def packet_reaches_endpoint():
                globals_.event_manager.log(
                        '{} delivered {} to the endpoint associated with {}'.format(
                            self.id_, packet, dst_endpoint.device.id_))
                dst_endpoint.device.receive_packet(packet)
                self.total_data_sent += packet.size
                globals_.stats_manager.notify(self.data_sent_graph_tag, self.total_data_sent)
                globals_.stats_manager.notify(self.rate_data_sent_graph_tag, self.total_data_sent)
            globals_.event_manager.add(self.delay, packet_reaches_endpoint)
        time_transmission_finishes = self.packet_transmitting.size / self.rate
        globals_.event_manager.add(time_transmission_finishes, packet_finishes_transmitting)

    def measure_cost(self):
        current_time = globals_.event_manager.get_time()
        if not self.cost_measurements or self.cost_measurements[-1][0] != current_time:
            cost_measurement = (self.endpoint1.get_buffer_occupancy_percentage() +
                                self.endpoint2.get_buffer_occupancy_percentage()) / self.rate
            self.cost_measurements.append((current_time, cost_measurement))

    def get_cost(self):
        if not self.cost_measurements:
            return float('inf')
        return sum([tup[1] for tup in self.cost_measurements]) / len(self.cost_measurements)

    def reset_cost(self):
        '''
        This should be called when routers reset reset their routing tables.
        Resets cost measurements.
        '''
        current_time = globals_.event_manager.get_time()
        if self.cost_measurements and self.cost_measurements[-1][0] == current_time:
            self.cost_measurements = [self.cost_measurements[-1]]
        else:
            self.cost_measurements = []

    def act(self):
        if self.waiting_prop_time or self.packet_transmitting:
            return False
        if self.waiting_to_decide_direction:
            assert self.src_dst_endpoints is None
            self.src_dst_endpoints = self.get_src_dst_endpoints()
            if self.src_dst_endpoints is None:
                # There is still nothing to send, so we are still waiting to decide direction
                return False
            self.waiting_to_decide_direction = False

        # We know what direction we want to send
        src, dst = self.src_dst_endpoints
        max_size_can_send = self.max_bits_sent_in_sequence - self.bits_sent_in_sequence
        if not src.buffer or src.peek_lra()[0].size > max_size_can_send:
            # We can't send any more in this sequence
            # So, wait a propagation time, and then (probably) switch src and dst
            self.waiting_prop_time = True
            self.bits_sent_in_sequence = 0
            def done_waiting_prop_time():
                self.waiting_prop_time = False
                if dst.buffer:
                    # If the other buffer has stuff to send, let switch direction to let it send
                    self.src_dst_endpoints = dst, src
                    return
                if src.buffer:
                    # If the other buffer has no stuff to send, but this one
                    # does, then maintain direction
                    return
                # There is nothing to send
                self.src_dst_endpoints = None
                self.waiting_to_decide_direction = True
            globals_.event_manager.add(self.delay, done_waiting_prop_time)
            # Our action didn't affect anything else, so return False
            return False

        self.bits_sent_in_sequence += src.peek_lra()[0].size
        self.send(src, dst)
        return True
