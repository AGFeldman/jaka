from link import Link
from host import Host
from router import Router
from flow import Flow


class Network(object):
    '''
    Represents a collection of Devices and Links constituting
    a network. Also includes information about the Flows
    travelling along the network.
    '''
    def __init__(self):
        self.devices = dict()
        self.links = dict()
        self.flows = dict()

    def add_host(self, id_):
        # Adds a Host object to the network
        if id_ in self.devices:
            raise ValueError("Duplicate Host/Router ID")
        self.devices[id_] = Host(id_)

    def add_router(self, id_):
        # Adds a Router object to the network
        if id_ in self.devices:
            raise ValueError("Duplicate Host/Router ID")
        self.devices[id_] = Router(id_)

    def add_link(self, id_, dev_id_1, dev_id_2, rate, delay, buf_size):
        # Adds a Link object to the network
        if id_ in self.links:
            raise ValueError("Duplicate Link ID")
        if dev_id_1 not in self.devices or \
           dev_id_2 not in self.devices:
            raise ValueError("Specified Hosts/Routers not Initialized")
        self.links[id_] = Link(id_=id_,
                               device1=self.devices[dev_id_1],
                               device2=self.devices[dev_id_2],
                               rate=rate,
                               delay=delay,
                               buffer_size=buf_size)

    def add_flow(self, id_, start, amount, src_id, dst_id):
        # Adds a Flow to the network
        if id_ in self.flows:
            raise ValueError("Duplicate Flow ID")
        if src_id not in self.devices or \
           not isinstance(self.devices[src_id], Host):
            raise ValueError("Invalid Source Host ID")
        if dst_id not in self.devices or \
           not isinstance(self.devices[dst_id], Host):
            raise ValueError("Invalid Destination Host ID")
        self.flows[id_] = Flow(id_=id_,
                               start=start,
                               amount=amount,
                               src_obj=self.devices[src_id],
                               dst_obj=self.devices[dst_id])

    def get_actors(self):
        # Returns a list of all actors in the network.
        # This includes Hosts, Routers, and Links
        return self.devices.values() + self.links.values()

    def get_flows(self):
        # Returns a list of the flows.
        return self.flows.values()

    def gen_dot(self):
        # Generate a DOT representation of the network and
        # return it as a string.
        dot = ""
        dot += "graph {\n"
        for id_, dev in self.devices.iteritems():
            if isinstance(dev, Host):
                dot += "%s [shape = box];" % id_
            elif isinstance(dev, Router):
                dot += "%s [shape = oval];" % id_
            else:
                dot += "%s ;" % id_

        for id_, link in self.links.iteritems():
            dot += "%s -- %s [label = \"%s\"] ;" % \
                   (link.endpoint1.device.id_,
                    link.endpoint2.device.id_,
                    link.id_)
        dot += "}"
        return dot

    def print_dot(self):
        # Generate a DOT representation of the network and
        # write to stdout
        print self.gen_dot()
