class Device(object):
    '''
    Hosts, Routers, and Switches are Devices
    '''
    def __init__(self, id_):
        self.id_ = id_

    def __str__(self):
        return self.id_

    def plug_in_link(self, link_endpoint):
        '''
        link_endpoint should be a LinkEndpoint
        '''
        raise NotImplementedError

    def send_packet(self, packet):
        raise NotImplementedError

    def recieve_packet(self, packet):
        raise NotImplementedError
