from __future__ import division

import random

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

        if globals_.stats_manager:
            self.packets_dropped_graph_tag = globals_.stats_manager.new_graph(
                    title='Number of Packets Dropped on {}/{} endpoint'.format(
                        self.link.id_, self.device.id_),
                    ylabel='Number of Packets Dropped')
            self.buffer_occupancy_graph_tag = globals_.stats_manager.new_graph(
                    title='Buffer Occupancy for {}/{} endpoint'.format(
                        self.link.id_, self.device.id_),
                    ylabel='Buffer Occupancy (bits)')
        self.num_packets_dropped = 0

    def get_buffer_occupancy(self):
        return self.buffer_size - self.buffer_space_free

    def get_buffer_occupancy_percentage(self):
        return self.get_buffer_occupancy() / self.buffer_size

    def notify_buffer_occupancy(self):
        globals_.stats_manager.notify(self.buffer_occupancy_graph_tag,
                                      self.get_buffer_occupancy())

    def receive_from_device(self, packet):
        # TODO(agf): Add fields 'stats_packets_received' and 'stats_packets_dropped'
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

    def get_default_cost(self):
        return self.link.get_default_cost()

    def get_cost(self):
        '''
        This could be many different things, such as queue length, average
        queueing delay, or transmission+propagation time
        Or it could be constant ("one link is one hop")
        '''
        return self.link.get_cost()

    def reset_cost(self):
        self.link.reset_cost()


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

        if globals_.stats_manager:
            self.data_sent_graph_tag = globals_.stats_manager.new_graph(
                    title='Total Bits Sent Over {}'.format(self.id_),
                    ylabel='Bits'
            )
            self.rate_data_sent_graph_tag = globals_.stats_manager.new_graph(
                    title='Rate of Sending Data Over {}'.format(self.id_),
                    ylabel='Rate (bits/second)',
                    is_rate=True
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

        # TODO(agf): Make this global or user-specifiable
        self.max_bits_sent_in_sequence = 10 ** 5
        self.bits_sent_in_sequence = 0
        self.packet_transmitting = None
        self.waiting_prop_time = False
        self.waiting_to_decide_direction = True
        self.src_dst_endpoints = None

        self.cost_measurements = []
        self.reset_cost()

    def get_src_dst_endpoints(self):
        '''
        Used to determine what direction a packet should travel if we're
        otherwise undecided
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

    def get_default_cost(self):
        return 0.5

    def get_cost(self):
        '''
        A cost measurement is taken.
        Cost measurement is the average of the buffer occupancy percentages.
        Returns cost, which is based on cost measurements.
        '''
        cost_measurement = (self.endpoint1.get_buffer_occupancy_percentage() +
                            self.endpoint2.get_buffer_occupancy_percentage()) / 2
        self.cost_measurements.append((globals_.event_manager.get_time(), cost_measurement))
        return self.get_cost_from_measurements()

    def get_cost_from_measurements(self):
        '''
        Cost is the average of the cost measurements, with each measurment
        weighted by the time since the previous measurement.
        '''
        reset_time = self.cost_measurements[0][0]
        prev_time = reset_time
        weighted_measurement_sum = 0
        for time, measurement in self.cost_measurements:
            weighted_measurement_sum += (time - prev_time) * measurement
            prev_time = time
        return weighted_measurement_sum / (time - reset_time)

    def reset_cost(self):
        '''
        This should be called when routers reset reset their routing tables.
        Resets cost measurements.
        '''
        self.cost_measurements = [(globals_.event_manager.get_time(), 0)]

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
