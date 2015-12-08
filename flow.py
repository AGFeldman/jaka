from __future__ import division

import globals_

from packet import DataPacket, AckPacket


class RTTE(object):
    '''
    Keep a Round Trip Time estimate
    This class should only be used with `from __future__ import division`
    '''
    def __init__(self, flow):
        self.flow = flow
        self.max_num_data_points = globals_.NUM_OBSERVATIONS_FOR_RTTE
        if self.flow.protocol == 'FAST':
            # There is no set maximum number of data points, but TCP-FAST will
            # call RTTE.reset() after updating its window size
            self.max_num_data_points = float('inf')
        self.min_rtt_observed = None
        self.max_rtt_observed = None
        self.reset()

    def reset(self):
        self.estimate_with_no_data = globals_.INITIAL_RTT_ESTIMATE
        self.data = []
        if self.flow.protocol == 'FAST':
            self.n_missed_acks = 0

    def get_estimate(self):
        if not self.data:
            return self.estimate_with_no_data
        n_observations = len(self.data)
        sum_of_observations = sum((rtt for rtt in self.data))
        if self.flow.protocol == 'FAST':
            n_observations += self.n_missed_acks
            sum_of_observations += (self.n_missed_acks * globals_.MISSED_ACK_RTT_FACTOR *
                                    self.get_max())
        return sum_of_observations / n_observations

    def get_base(self):
        '''
        Return a number that roughly corresponds to the smallest amount of time
        that we expect a round trip to take
        '''
        if self.min_rtt_observed is None:
            return globals_.INITIAL_RTT_ESTIMATE
        return self.min_rtt_observed

    def get_max(self):
        if self.max_rtt_observed is None:
            return globals_.INITIAL_RTT_ESTIMATE
        return self.max_rtt_observed

    def log_rtte(self):
        globals_.event_manager.log('{} RTT estimate is {}'.format(self.flow.id_,
                                                                  self.get_estimate()))

    def update_missed_ack(self):
        if not self.data:
            self.estimate_with_no_data += globals_.INITIAL_RTT_ESTIMATE
        if self.flow.protocol == 'FAST':
            self.n_missed_acks += 1

    def update_rtt_datapoint(self, rtt_value):
        # Add the data point to self.data
        self.data.append(rtt_value)
        if len(self.data) > self.max_num_data_points:
            del self.data[0]
        # Update self.min_rtt_observed
        if self.min_rtt_observed is None:
            self.min_rtt_observed = rtt_value
        else:
            self.min_rtt_observed = min((self.min_rtt_observed, rtt_value))
        # Update self.max_rtt_observed
        if self.max_rtt_observed is None:
            self.max_rtt_observed = rtt_value
        else:
            self.max_rtt_observed = max((self.max_rtt_observed, rtt_value))


class Flow(object):
    def __init__(self, id_=None, start=None, amount=None, src_obj=None, dst_obj=None,
                 protocol=None, alpha=None):
        '''
        id_ is e.g. "F1"
        start is the time that the flow should start, in seconds
        amount is the amount of data to send, in bits
        src_obj is the Host object for the source
        dst_obj is the Host object for the destination
        protocol is either "RENO" or "FAST"

        public members:
            self.finished: Indicates whether the flow has finished transmitting all packets
        '''
        self.id_ = id_
        self.start = start
        self.amount = amount
        self.src_obj = src_obj
        self.dst_obj = dst_obj
        self.protocol = protocol
        self.alpha = alpha
        assert self.protocol in ('RENO', 'FAST')

        self.init_window_size()

        # Round trip time estimate
        self.rtte = RTTE(self)

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

        # TCP States (affect how window is changed)
        self.slow_start = True
        self.congestion_avoidance = False
        self.ssthresh = float('inf')

        self.ndups = 0
        self.dup_id = -1
        self.fast_recovery = False
        self.time_last_fr = -1

    def init_window_size(self):
        self.window_size = 1
        self.window_size_float = float(1)

    def update_window_size_missed_ack(self):
        '''
        This is called when waiting to receive an ack for a sent packet times out
        Set ssthresh to half of the current window size,
        unless a timeout happened within the past 0.5 seconds or rtte,
        then set the window size to 1
        '''
        if self.fast_recovery:
            self.exit_fast_recovery()

        time = globals_.event_manager.get_time()
        if time - self.time_of_last_window_reduction > max(0.5, self.rtte.get_estimate()):
            self.time_of_last_window_reduction = time
            self.ssthresh = max(((self.window_size // 2) + (self.window_size % 2), 1))
            # TCP-FAST doesn't cut window size upon missed ack
            if self.protocol == 'RENO':
                self.set_window_size(1)
            globals_.event_manager.log(
                '{}: Due to missed ack, set w={} and ssthresh={}'.format(
                    self.id_, self.window_size, self.ssthresh))

        self.retransmit()

    def retransmit(self):
        self.packets_waiting_for_acks = dict()
        globals_.event_manager.log(
            '{} is retransmitting all in txwindow, w={} ssthresh={}'.format(
                self.id_, self.window_size, self.ssthresh))
        assert self.transmit_window_start <= len(self.packets_to_send)
        if (globals_.event_manager.get_time() > self.start and
                self.transmit_window_start == len(self.packets_to_send) and
                not self.packets_waiting_for_acks):
            self.finished = True
        elif self.transmit_window_start < len(self.packets_to_send):
            end_range = min(self.transmit_window_start + self.window_size,
                            len(self.packets_to_send))
            for id_ in xrange(self.transmit_window_start, end_range):
                packet = self.packets_to_send[id_]
                self.send_packet(packet)
                globals_.event_manager.log('{} sent packet {}'.format(self.id_, packet))

    def set_window_size(self, size):
        self.window_size = size
        self.adjust_state(size)
        globals_.stats_manager.notify(self.window_size_graph_tag, size)

    def enter_congestion_avoidance(self):
        globals_.event_manager.log('{} is entering CA, w={}'.format(self.id_, self.window_size))
        self.slow_start = False
        self.congestion_avoidance = True
        self.window_size_float = self.window_size

    def adjust_state(self, size):
        if size < self.ssthresh:
            self.slow_start = True
            self.congestion_avoidance = False
        elif (size >= self.ssthresh) and self.slow_start:
            self.enter_congestion_avoidance()

    # TODO(agf): Instead of using this beat, we could calculate window size
    # every time that get_window_size() is called
    def start_FAST_window_size_update_beat(self):
        '''
        In TCP-FAST, window size is given by a formula
        Establish a beat that uses this formula to update the window size every 50 ms
        '''
        assert self.protocol == 'FAST'
        def beat():
            if (self.congestion_avoidance):
                self.window_size_float = ((self.rtte.get_base() / self.rtte.get_estimate())
                                          * self.window_size_float + self.alpha)
                self.set_window_size(int(self.window_size_float // 1))
                globals_.event_manager.log('{} window size is now {}'.format(
                    self.id_, self.window_size))
            self.rtte.reset()
            globals_.event_manager.add(0.050, beat)
        globals_.event_manager.add(0.050, beat)

    def fast_retransmit(self, packet_id):
        # DEBUG(jg)
        globals_.event_manager.log(
            'WINDOW fast_retransmitting pkt_id={} w={} ssthresh={}'.format(
                packet_id, self.window_size, self.ssthresh))
        # ENDEBUG
        packet = self.packets_to_send[packet_id]
        assert isinstance(packet, DataPacket)
        self.send_packet(packet)
        globals_.event_manager.log('{} fast retransmitted packet {}'.format(self.id_, packet))

    def enter_fast_recovery(self):
        # Do not enter fr if did it recently
        if (globals_.event_manager.get_time() - self.time_last_fr <
                max(0.5, 3 * self.rtte.get_estimate())):
            return

        self.time_last_fr = globals_.event_manager.get_time()
        self.ssthresh = max((self.window_size // 2, 2))
        self.set_window_size(self.ssthresh + self.ndups)
        # DEBUG(jg)
        globals_.event_manager.log(
            'WINDOW entering fast recovery w={} set ssthresh:={}'.format(
                self.window_size, self.ssthresh))
        # ENDEBUG
        self.fast_recovery = True

    def exit_fast_recovery(self):
        assert self.ssthresh != float('inf')
        self.set_window_size(self.ssthresh)
        self.window_size_float = float(self.window_size)
        # DEBUG(jg)
        globals_.event_manager.log(
            'WINDOW exiting fast recovery w:={} set ssthresh={}'.format(
                self.window_size, self.ssthresh))
        # ENDEBUG
        self.ndups = 0
        self.dup_id = -1
        self.fast_recovery = False

    def update_packets_waiting_for_ack(self, next_expected):
        for id_ in self.packets_waiting_for_acks.keys():
            if id_ < next_expected:
                del self.packets_waiting_for_acks[id_]

    def receive_ack(self, packet):
        assert isinstance(packet, AckPacket)
        assert packet.dst == self.src_obj.id_
        globals_.event_manager.log(
                '{} received ack for {}; next_expected={}; w_size={}; ssthresh={}'.format(
                    self.id_, packet.id_, packet.next_expected, self.window_size, self.ssthresh))

        # Update ndups
        if self.congestion_avoidance and self.protocol == 'RENO':
            if packet.next_expected == self.dup_id:
                self.ndups = self.ndups + 1
            elif packet.next_expected > self.dup_id:
                self.ndups = 1
                self.dup_id = packet.next_expected

            if self.ndups == 3 and packet.next_expected < len(self.packets_to_send):
                self.enter_fast_recovery()
                self.fast_retransmit(packet.next_expected)

            if self.fast_recovery and self.ndups < 3:
                self.exit_fast_recovery()

        self.update_transmit_window(packet.next_expected)
        if packet.id_ not in self.packets_waiting_for_acks:
            # This could happen if the ack comes too late
            globals_.event_manager.log('{} received ack for {}'.format(self.id_, packet))
            return
        globals_.event_manager.log('{} received ack for {}'.format(self.id_, packet))
        data_packet, time_sent = self.packets_waiting_for_acks[packet.id_]
        assert packet.src == data_packet.dst and packet.dst == data_packet.src
        if data_packet.num_times_sent == 1:
            rtt = globals_.event_manager.get_time() - time_sent
            self.rtte.update_rtt_datapoint(rtt)
            globals_.stats_manager.notify(self.rt_packet_delay_graph_tag, rtt)

        self.update_packets_waiting_for_ack(packet.next_expected)

    def send_packet(self, packet):
        assert isinstance(packet, DataPacket)
        globals_.event_manager.log(
                '{} is sending packet {}; w_start={}; w_size={}; ssthresh={}'.format(
                    self.id_, packet.id_, self.transmit_window_start, self.window_size,
                    self.ssthresh))
        self.src_obj.send_packet(packet)
        packet.num_times_sent += 1

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
                # Removing packet from the dictionary of packets waiting for acks allows
                # us to re-transmit the packet
                del self.packets_waiting_for_acks[packet.id_]
                self.update_window_size_missed_ack()
            else:
                globals_.event_manager.log(
                        '{} is due to receive an ack for {}, has already received it'.format(
                            self.id_, packet.id_))
        # Wait 3 times the round-trip-time-estimate
        wait_time = 3 * self.rtte.get_estimate()
        packet.timeout = globals_.event_manager.get_time() + wait_time
        globals_.event_manager.add(wait_time, ack_is_due)

    def act(self):
        acted = False
        assert self.transmit_window_start <= len(self.packets_to_send)
        if (globals_.event_manager.get_time() > self.start and
                self.transmit_window_start == len(self.packets_to_send) and
                not self.packets_waiting_for_acks):
            self.finished = True
            return False
        elif self.transmit_window_start < len(self.packets_to_send):
            end_range = min(self.transmit_window_start + self.window_size,
                            len(self.packets_to_send))
            for id_ in xrange(self.transmit_window_start, end_range):
                if id_ not in self.packets_waiting_for_acks:
                    packet = self.packets_to_send[id_]
                    self.send_packet(packet)
                    globals_.event_manager.log('{} sent packet {}'.format(self.id_, packet))
                    acted = True
        return acted

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
            if self.protocol == 'FAST':
                self.start_FAST_window_size_update_beat()
        globals_.event_manager.add(self.start, setup)

    def log_packet_received(self):
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

    def update_transmit_window(self, ack_next_expected):
        if self.fast_recovery:
            if ack_next_expected > self.transmit_window_start:
                self.transmit_window_start = ack_next_expected

            self.set_window_size(self.ssthresh + self.ndups)
            # DEBUG(jg)
            globals_.event_manager.log(
                'WINDOW: updating window in FAST_RECOVERY, ndup={}, w:={}, ssthresh={}'.format(
                    self.ndups, self.window_size, self.ssthresh))
            # ENDEBUG(jg)
        elif ack_next_expected > self.transmit_window_start:
            self.transmit_window_start = ack_next_expected
            # If in slow start mode, increment window on successful ack
            # This results in window doubling every RTT
            if self.slow_start:
                self.set_window_size(self.window_size + 1)
                # DEBUG(jg)
                globals_.event_manager.log(
                    'WINDOW: updating window in SLOW_START w = w + 1, w:={}, ssthresh={}'.format(
                        self.window_size, self.ssthresh))
                # ENDEBUG(jg)
            elif self.congestion_avoidance and self.protocol == 'RENO':
                self.window_size_float += 1.0 / self.window_size_float
                self.set_window_size(int(self.window_size_float // 1))
                # DEBUG(jg)
                globals_.event_manager.log(
                    'WINDOW: updating window in CONGESTION_AVOIDANCE w = w + 1/w'
                    + ', w:={}, ssthresh={}'.format(
                        self.window_size, self.ssthresh))
                # ENDEBUG(jg)
