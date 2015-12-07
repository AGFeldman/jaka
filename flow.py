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
        self.basertt = self.estimate
        self.ndatapoints = 0

        # TODO(jg): remove
        # Basertt is calculated as min of the last base_calc_range rtts
        # self.base_calc_range = 10
        # self.stored_rtts = []
        # for i in xrange(self.base_calc_range):
        #     self.stored_rtts.append(self.estimate)

    def update_missed_ack(self):
        if self.ndatapoints == 0:
            self.estimate += globals_.INITIAL_RTT_ESTIMATE

    def no_op(self):
        pass

    def update_basertt(self, rtt):
        # TODO(jg): remove/decide if use (basertt is min of last X rtts)
        # self.stored_rtts[self.ndatapoints % self.base_calc_range] = rtt
        # self.basertt = min(self.stored_rtts)
        self.basertt = min((self.basertt, rtt))
        
    def update_rtt_datapoint(self, rtt):
        self.ndatapoints += 1
        if self.ndatapoints == 1:
            self.estimate = rtt
            self.basertt = self.estimate
        else:
            # See https://www.stat.wisc.edu/~larget/math496/mean-var.html for
            # this formula for updating means
            self.estimate = self.estimate + (rtt - self.estimate) / self.ndatapoints
            # DEBUG(jg)
            globals_.event_manager.log('WINDOW update rtte to {}'.format(self.estimate))
            # ENDEBUG
            # Update basertt
            self.update_basertt(rtt)
        # We no longer need to perform updates when acks are missed
        self.update_missed_ack = self.no_op


class Flow(object):
    def __init__(self, id_=None, start=None, amount=None, src_obj=None, dst_obj=None,
                 protocol=None):
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
        assert self.protocol in ('RENO', 'FAST')

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
        # self.packets_ackd_out_of_order = []

        # TCP States (affect how window is changed)
        self.slow_start = True
        self.congestion_avoidance = False
        self.ssthresh = float('inf')

        self.ndups = 0
        self.dup_id = -1
        self.fast_recovery = False
        self.time_last_fr = -1

        # TCP FAST params
        self.tcp_fast = True
        self.alpha = 10

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
        if time - self.time_of_last_window_reduction > max(0.5, self.rtte.estimate):
            self.time_of_last_window_reduction = time
            new_size = max(((self.window_size // 2) + (self.window_size % 2), 1))
            # print 'w={}, new_size={}'.format(self.window_size, new_size)
            assert new_size >= 1
            # DEBUG(jg)
            globals_.event_manager.log(
                'WINDOW timed out, setting w:=1 ssthresh:={}'.format(new_size))
            # ENDEBUG
            self.ssthresh = new_size
            self.set_window_size(1)

        self.retransmit()

    def retransmit(self):
        self.packets_waiting_for_acks = dict()
        # DEBUG(jg)
        globals_.event_manager.log(
            'WINDOW retransmitting all in txwindow, w={} ssthresh:={}'.format(
                self.window_size, self.ssthresh))
        # ENDEBUG
        assert self.transmit_window_start <= len(self.packets_to_send)
        if globals_.event_manager.get_time() > self.start \
           and (self.transmit_window_start == len(self.packets_to_send)) \
           and not self.packets_waiting_for_acks:
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
        globals_.event_manager.log('WINDOW entering CA, w = {}'.format(self.window_size))
        self.slow_start = False
        self.congestion_avoidance = True
        self.window_size_float = self.window_size

    def adjust_state(self, size):
        if size < self.ssthresh:
            self.slow_start = True
            self.congestion_avoidance = False
        elif (size >= self.ssthresh) and self.slow_start:
            self.enter_congestion_avoidance()

    # TODO(jg): remove this; we no longer grow window size like this
    # Keeping this here because may use for FAST-TCP periodic window updates
    def start_growing_window_size(self):
        # Window size grows by 1 every round-trip-time estimate
        # TODO(agf): If round-trip-time estimate drops sharply, window size
        # still won't increase until it was last scheduled to increase
        def grow():
            # self.set_window_size(self.window_size + 1)
            # TCP FAST grow function

            # DEBUG(jg)
            old_window = self.window_size
            old_window_float = self.window_size_float
            # ENDEBUG(jg)
            if (self.congestion_avoidance):
                self.window_size_float = ((self.rtte.basertt / self.rtte.estimate) * self.window_size_float + self.alpha)
                self.set_window_size(int(self.window_size_float // 1))
                # DEBUG(jg)
                globals_.event_manager.log(
                    'WINDOW  TCP_FAST growth, base={}, est={}, base/est={}, old_wf={}, new_wf={},        old_w={}, new_w={}'
                    .format(self.rtte.basertt, self.rtte.estimate,
                            self.rtte.basertt / self.rtte.estimate,
                            old_window_float, self.window_size_float,
                            old_window, self.window_size)
                )
                # ENDEBUG

            globals_.event_manager.log('{} window size is now {}'.format(
                self.id_, self.window_size))
            globals_.event_manager.add(0.050, grow)
        globals_.event_manager.add(self.rtte.estimate, grow)

    def fast_retransmit(self, packet_id):
        # DEBUG(jg)
        globals_.event_manager.log(
            'WINDOW fast_retransmitting pkt_id={} w={} ssthresh={}'.format(
                packet_id, self.window_size, self.ssthresh))
        # ENDEBUG
        packet = self.packets_to_send[packet_id]
        assert isinstance(packet, DataPacket)
        self.send_packet(packet)
        # set new timeout times
        # for id_ in self.packets_waiting_for_acks.keys():
        #     self.reset_timeout(self.packets_to_send[id_])

        globals_.event_manager.log('{} fast retransmitted packet {}'.format(self.id_, packet))

    def enter_fast_recovery(self):
        # Do not enter fr if did it recently
        if globals_.event_manager.get_time() - self.time_last_fr \
           < max(0.5, 3*self.rtte.estimate):
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

        # DEBUG(jg)
        globals_.event_manager.log(
            'WINDOW                  RECEIVED ack pkt_id={}, next_expected={}, w:={} ssthresh={}'
            .format(packet.id_, packet.next_expected, self.window_size, self.ssthresh))
        # ENDEBUG

        # Update ndups
        if self.congestion_avoidance and not self.tcp_fast:
            if packet.next_expected == self.dup_id:
                self.ndups = self.ndups + 1
            elif packet.next_expected > self.dup_id:
                self.ndups = 1
                self.dup_id = packet.next_expected

            if self.ndups == 3 and packet.next_expected < len(self.packets_to_send):
                self.enter_fast_recovery()
                # self.retransmit()
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
        if data_packet.times_sent == 1:
            rtt = globals_.event_manager.get_time() - time_sent
            self.rtte.update_rtt_datapoint(rtt)
            globals_.stats_manager.notify(self.rt_packet_delay_graph_tag, rtt)

        # del self.packets_waiting_for_acks[packet.id_]
        self.update_packets_waiting_for_ack(packet.next_expected)

    def reset_timeout(self, packet):
        assert isinstance(packet, DataPacket)
        # DEBUG(jg)
        globals_.event_manager.log(
            'WINDOW resetting timeout pkt_id={}; w_start = {}, w:={} set ssthresh={}'.format(
                packet.id_, self.transmit_window_start, self.window_size, self.ssthresh))
        # ENDEBUG
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
                # DEBUG(jg)
                globals_.event_manager.log('WINDOW timeout on pkt_id={}'.format(packet.id_))
                # ENDEBUG
                self.update_window_size_missed_ack()
                # self.retransmit()
            else:
                globals_.event_manager.log(
                        '{} is due to receive an ack for {}, has already received it'.format(
                            self.id_, packet.id_))
        # Wait 3 times the round-trip-time-estimate
        packet.timeout = globals_.event_manager.get_time() + 3 * self.rtte.estimate
        globals_.event_manager.add(3 * self.rtte.estimate, ack_is_due)

    def send_packet(self, packet):
        assert isinstance(packet, DataPacket)
        # DEBUG(jg)
        globals_.event_manager.log(
            'WINDOW SENDING                pkt_id={}; w_start = {}, w:={} set ssthresh={}'.format(
                packet.id_, self.transmit_window_start, self.window_size, self.ssthresh))
        # ENDEBUG
        self.src_obj.send_packet(packet)
        packet.times_sent = packet.times_sent + 1

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
                # DEBUG(jg)
                globals_.event_manager.log('WINDOW timeout on pkt_id={}'.format(packet.id_))
                # ENDEBUG
                self.update_window_size_missed_ack()
                # self.retransmit()
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
        if globals_.event_manager.get_time() > self.start \
           and (self.transmit_window_start == len(self.packets_to_send)) \
           and not self.packets_waiting_for_acks:
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
        # if not self.packets_to_send:
        #     if not self.packets_waiting_for_acks \
        #        and globals_.event_manager.get_time() > self.start:
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
            # TODO(jg): remove this; we no longer grow window size like this
            if self.tcp_fast:
                self.start_growing_window_size()
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

    # # This would be useful if we do selective acknowledgements
    # def update_transmit_window(self, packet_id):
    #     if packet_id == self.transmit_window_start:
    #         self.transmit_window_start += 1
    #         while self.transmit_window_start in self.packets_ackd_out_of_order:
    #             self.packets_ackd_out_of_order.remove(self.transmit_window_start)
    #             self.transmit_window_start += 1
    #     elif packet_id not in self.packets_ackd_out_of_order \
    #          and packet_id > self.transmit_window_start:
    #         self.packets_ackd_out_of_order.append(packet_id)

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
            elif self.congestion_avoidance and not self.tcp_fast:
                self.window_size_float += 1.0 / self.window_size_float
                self.set_window_size(int(self.window_size_float // 1))
                # DEBUG(jg)
                globals_.event_manager.log(
                    'WINDOW: updating window in CONGESTION_AVOIDANCE w = w + 1/w'
                    + ', w:={}, ssthresh={}'.format(
                        self.window_size, self.ssthresh))
                # ENDEBUG(jg)
