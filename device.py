class Device(object):
    '''
    Hosts, Routers, and Switches are Devices
    self.ports maps integers to LinkEndpoints
    '''
    def __init__(self, id_=None):
        self.id_ = id_
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
