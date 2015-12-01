from __future__ import division

import globals_

from packet import DataPacket, AckPacket


class RTTE(float):
    '''
    Keep a Round Trip Time estimate
    This class should only be used with `from __future__ import division`
    Public members:
        self.estimate
    '''
    def __init__(self):
        # Initial estimate is 100 ms
        self.estimate = globals_.INITIAL_RTT_ESTIMATE
        self.ndatapoints = 0

    def update_missed_ack(self):
        if self.ndatapoints == 0:
            self.estimate += globals_.INITIAL_RTT_ESTIMATE

    def no_op(self):
        pass

    def update_rtt_datapoint(self, rtt):
        self.ndatapoints += 1
        if self.ndatapoints == 1:
            self.estimate = rtt
        else:
            # See https://www.stat.wisc.edu/~larget/math496/mean-var.html for
            # this formula for updating means
            self.estimate = self.estimate + (rtt - self.estimate) / self.ndatapoints
        # We no longer need to perform updates when acks are missed
        self.update_missed_ack = self.no_op


class Flow(object):
    def __init__(self, id_=None, start=None, amount=None, src_obj=None, dst_obj=None):
        '''
        id_ is e.g. "F1"
        start is the time that the flow should start, in seconds
        amount is the amount of data to send, in bits
        src_obj is the Host object for the source
        dst_obj is the Host object for the destination

        public members:
            self.finished: Indicates whether the flow has finished transmitting all packets
        '''
        self.id_ = id_
        self.start = start
        self.amount = amount
        self.src_obj = src_obj
        self.dst_obj = dst_obj

        self.init_window_size()

        # Round trip time estimate
        self.rtte = RTTE()

        self.packets_to_send = []
        # packets_waiting_for_acks is a map from packet_id -> (packet_obj, time_packet_was_sent)
        self.packets_waiting_for_acks = dict()

        # For statistics
        self.window_size_graph_tag = globals_.stats_manager.new_graph(
            title='Window Size for Flow %s' % self.id_,
            ylabel='Window size'
        )
        self.num_packets_received_graph_tag = globals_.stats_manager.new_graph(
            title='Number of Data Packets received for Flow %s' % self.id_,
            ylabel='Number of data packets received'
        )
        self.rate_packets_received_graph_tag = globals_.stats_manager.new_graph(
            title='Rate of Data Packets received for flow %s' % self.id_,
            ylabel='Rate (packets / second)',
            is_rate=True
        )
        self.rt_packet_delay_graph_tag = globals_.stats_manager.new_graph(
            title='Round Trip Packet Delay for Flow %s' % self.id_,
            ylabel='Delay (seconds'
        )

        # Number of data packets that have been successfully received at destination
        self.num_packets_received = 0

        self.finished = False

        self.time_of_last_window_reduction = float('-inf')

        # Smallest sequence number that receiver hasn't received
        self.next_expected = 0
        self.packets_received_out_of_order = []

        # Start of transmit window (earliest unacknowledged sequence number)
        self.transmit_window_start = 0

        # If we eventually do selective acknowledgements
        #self.packets_ackd_out_of_order = []

    def init_window_size(self):
        self.window_size = 1

    def update_window_size_missed_ack(self):
        '''
        Cut the window size in half, unless the window size was halved within
        the previous 0.5 seconds
        '''
        time = globals_.event_manager.get_time()
        if time - self.time_of_last_window_reduction > 0.5:
            self.time_of_last_window_reduction = time
            new_size = (self.window_size // 2) + (self.window_size % 2)
            assert new_size >= 1
            self.set_window_size(new_size)

    def set_window_size(self, size):
        self.window_size = size
        globals_.stats_manager.notify(self.window_size_graph_tag, size)

    def start_growing_window_size(self):
        # Window size grows by 1 every round-trip-time estimate
        # TODO(agf): If round-trip-time estimate drops sharply, window size
        # still won't increase until it was last scheduled to increase
        def grow():
            self.set_window_size(self.window_size + 1)
            globals_.event_manager.log('{} window size is now {}'.format(
                self.id_, self.window_size))
            globals_.event_manager.add(self.rtte.estimate, grow)
        globals_.event_manager.add(self.rtte.estimate, grow)

    def receive_ack(self, packet):
        assert isinstance(packet, AckPacket)
        assert packet.dst == self.src_obj.id_
        self.update_transmit_window(packet.next_expected)
        if packet.id_ not in self.packets_waiting_for_acks:
            # This could happen if the ack comes too late
            globals_.event_manager.log('{} received ack for {}'.format(self.id_, packet))
            return
        globals_.event_manager.log('{} received ack for {}'.format(self.id_, packet))
        original_packet, time_sent = self.packets_waiting_for_acks[packet.id_]
        assert packet.src == original_packet.dst and packet.dst == original_packet.src
        rtt = globals_.event_manager.get_time() - time_sent
        self.rtte.update_rtt_datapoint(rtt)
        del self.packets_waiting_for_acks[packet.id_]
        globals_.stats_manager.notify(self.rt_packet_delay_graph_tag, rtt)

    def send_packet(self, packet):
        assert isinstance(packet, DataPacket)
        self.src_obj.send_packet(packet)
        self.packets_waiting_for_acks[packet.id_] = (packet, globals_.event_manager.get_time())
        def ack_is_due():
            # This packet could have been resent after this timeout event was created;
            # in that case, this timeout event is now invalid (real timeout should be later)
            if packet.timeout != globals_.event_manager.get_time():
                # TODO(jg): log this
                return
            if packet.id_ in self.packets_waiting_for_acks:
                globals_.event_manager.log(
                        '{} is due to receive an ack for {}, has not received it'.format(
                            self.id_, packet.id_))
                self.rtte.update_missed_ack()

                # We no longer use the packets_to_send as a queue
                # self.packets_to_send.insert(0, packet)

                # Remove from list of packets waiting for acks
                # This might be necessary to enable more sends, since sends can
                # only occur when #waiting_for_acks < window_size
                del self.packets_waiting_for_acks[packet.id_]
                self.update_window_size_missed_ack()
            else:
                globals_.event_manager.log(
                        '{} is due to receive an ack for {}, has already received it'.format(
                            self.id_, packet.id_))
        # Wait 3 times the round-trip-time-estimate
        packet.timeout = globals_.event_manager.get_time() + 3 * self.rtte.estimate
        globals_.event_manager.add(3 * self.rtte.estimate, ack_is_due)

    def act(self):
        acted = False
        assert self.transmit_window_start <= len(self.packets_to_send)
        if globals_.event_manager.get_time() > self.start and (self.transmit_window_start == len(self.packets_to_send)) and not self.packets_waiting_for_acks:
            self.finished = True
            return False
        elif self.transmit_window_start < len(self.packets_to_send):
            end_range = min(self.transmit_window_start + self.window_size, len(self.packets_to_send))
            for id_ in xrange(self.transmit_window_start, end_range):
                if id_ not in self.packets_waiting_for_acks:
                    packet = self.packets_to_send[id_]
                    self.send_packet(packet)
                    globals_.event_manager.log('{} sent packet {}'.format(self.id_, packet))
                    acted = True
        return acted
        # if not self.packets_to_send:
        #     if not self.packets_waiting_for_acks and globals_.event_manager.get_time() > self.start:
        #         self.finished = True
        #     return False
        # n_waiting_for_acks = len(self.packets_waiting_for_acks)
        # if n_waiting_for_acks >= self.window_size:
        #     return False
        # for _ in xrange(min((self.window_size - n_waiting_for_acks, len(self.packets_to_send)))):
        #     packet = self.packets_to_send.pop(0)
        #     self.send_packet(packet)
        #     globals_.event_manager.log('{} sent packet {}'.format(self.id_, packet))
        # return True

    def generate_packets_to_send(self):
        '''
        Fill self.packets with the packets that we want to send
        '''
        npackets = self.amount // globals_.DATA_PACKET_SIZE
        if self.amount % globals_.DATA_PACKET_SIZE != 0:
            npackets += 1
        for id_ in xrange(npackets):
            self.packets_to_send.append(DataPacket(id_=id_,
                                                   src=self.src_obj.id_,
                                                   dst=self.dst_obj.id_,
                                                   flow=self))

    def register_with_event_manager(self):
        def setup():
            self.generate_packets_to_send()
            self.start_growing_window_size()
        globals_.event_manager.add(self.start, setup)

    def log_packet_received(self):
        # DEBUG(jg)
        globals_.event_manager.log("GOT INTO flow.log_packet_received")
        # ENDEBUG
        self.num_packets_received += 1
        globals_.stats_manager.notify(self.num_packets_received_graph_tag,
                                      self.num_packets_received)
        globals_.stats_manager.notify(self.rate_packets_received_graph_tag,
                                      self.num_packets_received)

    def update_next_expected(self, packet_id):
        if packet_id == self.next_expected:
            self.next_expected += 1
            while self.next_expected in self.packets_received_out_of_order:
                self.packets_received_out_of_order.remove(self.next_expected)
                self.next_expected += 1
        elif packet_id not in self.packets_received_out_of_order and packet_id > self.next_expected: 
            self.packets_received_out_of_order.append(packet_id)
    
    ## This would be useful if we do selective acknowledgements
    # def update_transmit_window(self, packet_id):
    #     if packet_id == self.transmit_window_start:
    #         self.transmit_window_start += 1
    #         while self.transmit_window_start in self.packets_ackd_out_of_order:
    #             self.packets_ackd_out_of_order.remove(self.transmit_window_start)
    #             self.transmit_window_start += 1
    #     elif packet_id not in self.packets_ackd_out_of_order and packet_id > self.transmit_window_start: 
    #         self.packets_ackd_out_of_order.append(packet_id)

    def update_transmit_window(self, ack_next_expected):
        if ack_next_expected > self.transmit_window_start:
            self.transmit_window_start = ack_next_expected
