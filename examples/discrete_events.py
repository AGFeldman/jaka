# Test Case 0
# We pretend that a host sends data packets regularly (one packet every k
# milliseconds or something). Acks are sent back. If a host fails to get back
# an ack within a certain amount of time, it re-transmits the data packet (in
# addition to the one packet per k milliseconds that it might already be
# sending).
# The link magically knows about both of its buffers, and it sends the packet
# that was least recently added to one of its buffers.
#
# The only size units used internally are bytes (not MB or KB)
# The only time units used internally are seconds
# (So, the only rate units used internally are bytes per second)
#
# Design choice: Two objects may have references to each other iff the objects
# touch. So, hosts and link endpoints can have references to each other, but
# hosts and links cannot. Links and link endpoints can have references to each
# other.
# It would probably be cleanest to treat most object members as private, but
# I'm not doing that right now.
#
# Network equipment ids are strings like 'H1' and 'L1'
# Packet ids are integers
#
# Example usage of this example code:
# time python -m cProfile -s time discrete_events.py < /dev/null > out


from __future__ import division
import random
import sys


ACK_SIZE = 15  # or something
DATA_PACKET_SIZE = 1500  # or something

# These are heavy-handed simplifications
TIME_BETWEEN_SENDS = 1
TIME_TO_WAIT_UNTIL_ACK = 10
PORT = 0


class EventManager(object):
    '''
    Intended as singleton class

    One important field is self.actors. After each event is processed,
    EventManager calls the act() method on each actor in self.actors. It
    continues calling the act() method on each actor until no actors wish to
    act -- that is, until all act() calls return false.

    self.queue is maintained as a list of (time_of_exection, function,
    description) elements.
    '''

    def __init__(self, actors=None):
        self.actors = []
        if actors:
            self.actors = actors
        # Note: If queue grows huge, performance will suffer because growing
        # python lists is slow
        self.queue = []
        self.time = 0

        # Start by scheduling a no-op. This triggers a cascade of act() calls
        # on network equipment objects, as always happens when an event is
        # processed. This initial cascade can be used to schedule the setup for
        # any stuff like routing tables.
        # This is just an idea. It isn't used for anything in this example code.
        def no_op():
            pass
        self.add(0, no_op)

    def log(self, msg):
        print 'Time', self.get_time(), ':', msg

    def set_actors(self, actors):
        self.actors = actors

    def get_time(self):
        return self.time

    def add(self, time_until_action, action,):
        assert(time_until_action >= 0)
        self.queue.append((self.get_time() + time_until_action, action))
        self.queue.sort()

    def run(self):
        while self.queue:
            self.time, scheduled_action = self.queue.pop(0)
            scheduled_action()

            # Now we handle instantaneous actions.
            # The one actor acting could cause another actor to want to act, so
            # we loop until all no actors wish to act.
            keep_acting = True
            while keep_acting:
                keep_acting = False
                random.shuffle(self.actors)
                for actor in self.actors:
                    if actor.act():
                        keep_acting = True


class Packet(object):
    def __init__(self, id=None, src=None, dst=None, size=0, ack=False):
        '''
        id is used for both data packet and corresponding ack packet. This could change.
        src is source_host.id
        dst is destination_host.id
        size is packet size in bytes
        ack is True iff this packet is an acknowledgement
        '''
        self.id = id
        self.src = src
        self.dst = dst
        self.size = size
        self.ack = ack

    def __str__(self):
        if self.ack:
            return '({}, {}, {}, ack)'.format(self.id, self.src, self.dst)
        return '({}, {}, {})'.format(self.id, self.src, self.dst)


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
            self.buffer.append((packet, event_manager.get_time()))
            self.buffer_space_free -= packet.size
        else:
            event_manager.log('endpoint associated with {} dropped {}'.format(self.device.id, packet))

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
    def __init__(self, id=None, device1=None, device2=None, rate=0, delay=0, buffer_size=0):
        '''
        device1 and device2 should be Host, Router, or Switch objects
        rate is in bytes per second
        delay is in seconds
        buffer_size is in bytes

        self.state is either 'sending' or 'not_sending'
        '''
        self.id = id
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
            event_manager.log('{} delivered {} to the endpoint associated with {}'.format(self.id, self.packet_on_link, dst_endpoint.device.id))
            dst_endpoint.device.receive_packet(self.packet_on_link)
            self.packet_on_link = None
        event_manager.add(self.transit_time(self.packet_on_link), packet_reaches_endpoint)

    def act(self):
        if self.packet_on_link:
            return
        src_dst_endpoints = self.get_src_dst_endpoints()
        if src_dst_endpoints:
            self.send(*src_dst_endpoints)


class Device(object):
    '''
    Hosts, Routers, and Switches are Devices

    self.ports maps integers to LinkEndpoints
    '''
    def __init__(self, id=None):
        self.id = id
        # Currently, devices have an unlimited number of ports
        self.next_open_port = 0
        # map from port number to LinkEndpoint
        self.ports = dict()

    def plug_in_link(self, link_endpoint):
        '''
        link_endpoint should be a LinkEndpoint
        '''
        self.ports[self.next_open_port] = link_endpoint
        self.next_open_port += 1

    def send_packet(self, packet=None, port=None):
        raise NotImplementedError
        # TODO(agf): There could be a very small time that it takes to send
        # into link buffer, during which time the device might not be able to
        # receive from the link. Or maybe this is a lie.

    def recieve_packet(self, packet):
        # Should examine packet src and send ack
        raise NotImplementedError


class Host(Device):
    def __init__(self, id=None):
        super(Host, self).__init__(id=id)
        # maybe it should have a list of packets to send, a list of packets
        # recieved and not processed yet, and a set of packets sent and still
        # waiting for acks
        self.packets_to_send = []
        # map from packet id to packet
        # TODO(agf): This relies on packet ids being unique over all the
        # packets sent by any one host
        self.packets_waiting_for_acks = dict()
        self.next_unused_packet_id = 0
        self.in_sending_chain = False

    def generate_packet(self, dst_id):
        self.packets_to_send.append(Packet(id=self.next_unused_packet_id, src=self.id, dst=dst_id, size=DATA_PACKET_SIZE, ack=False))
        self.next_unused_packet_id += 1

    def generate_packets_to_send(self, dst_id, how_much_data):
        npackets = how_much_data // DATA_PACKET_SIZE
        if how_much_data % DATA_PACKET_SIZE != 0:
            npackets += 1
        for _ in xrange(npackets):
            self.generate_packet(dst_id)

    def receive_packet(self, packet):
        assert packet.dst == self.id
        if packet.ack:
            event_manager.log('{} received ack for {}'.format(self.id, packet))
            assert packet.id in self.packets_waiting_for_acks
            original_packet = self.packets_waiting_for_acks[packet.id]
            if packet.src == original_packet.dst and packet.dst == original_packet.src:
                del self.packets_waiting_for_acks[packet.id]
        else:
            # Send an ack
            ack = Packet(id=packet.id, src=self.id, dst=packet.src, size=ACK_SIZE, ack=True)
            # Schedule the ack to be the next packet sent
            self.packets_to_send.insert(0, ack)

    def send_packet(self, packet, port):
        self.ports[port].receive_from_device(packet)
        if not packet.ack:
            self.packets_waiting_for_acks[packet.id] = packet
            def ack_is_due():
                if packet.id in self.packets_waiting_for_acks:
                    event_manager.log('{} is due to receive an ack for {}, has not received it'.format(self.id, packet.id))
                    self.packets_to_send.insert(0, packet)
                else:
                    event_manager.log('{} is due to receive an ack for {}, has already received it'.format(self.id, packet.id))
            description = '{} is due to receive an ack for {}'.format(self.id, packet.id)
            event_manager.add(TIME_TO_WAIT_UNTIL_ACK, ack_is_due)

    def act(self):
        if not self.in_sending_chain and self.packets_to_send:
            self.in_sending_chain = True
            def send_packet_and_schedule_next_send():
                if not self.packets_to_send:
                    self.in_sending_chain = False
                    return
                packet = self.packets_to_send.pop(0)
                self.send_packet(packet, PORT)
                event_manager.log('{} sent packet {} on port {}'.format(self.id, packet, PORT))
                event_manager.add(TIME_BETWEEN_SENDS, send_packet_and_schedule_next_send)
            event_manager.add(0, send_packet_and_schedule_next_send)
            return True
        return False


def get_actors_flows(description):
    '''
    Takes a string |description| of the network topology and flows.
    Parses |description| and returns (actors, flows).
    |actors| is a list of objects associated with all the pieces of equipment
    in the network. These objects should be initialized.
    |flows| is a list of elements of the form (time, setup_function).
    |time| is the time, in seconds, at which the flow starts.

    In this example code, |description| is printed and then ignored, and
    hard-coded network topology and flow are used.

    TODO(agf): Other user inputs? Run for user-specified time?
    '''
    print 'Description:'
    print description

    host1 = Host(id='H1')
    host2 = Host(id='H2')
    link1 = Link(id='L1', device1=host1, device2=host2, rate=10**7, delay=0.010, buffer_size=64000)
    actors = [host1, host2, link1]

    def setup_flow1():
        host1.generate_packets_to_send(host2.id, 20 * 10**6)
    flows = [(0.5, setup_flow1)]

    return actors, flows


def simulate(description):
    '''
    Takes a string |description| of the network topology and flows.
    Runs the simulation!
    '''
    actors, flows = get_actors_flows(description)
    event_manager.set_actors(actors)
    for start_time, setup_flow in flows:
        event_manager.add(start_time, setup_flow)
    event_manager.run()


def main_setup():
    '''
    This should be called at the beginning of main if you're running unit tests
    or simulations.
    It seeds the random number generator and sets the global variable
    |event_manager|.
    We need to set |event_manager| for most class definitions and helper
    functions to make sense.
    '''
    random.seed(0)
    global event_manager
    event_manager = EventManager()


if __name__ == '__main__':
    main_setup()
    simulate(sys.stdin.read())
