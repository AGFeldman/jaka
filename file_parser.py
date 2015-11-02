import json
import check_json

from network import Network


class FileParser(object):
    '''
    Intended as a singleton class. The role of the file parser
    is to serve as a Network factory, which takes the name of
    a network specification file and returns a Network object
    '''

    def create_network(self, filename):
        with open(filename, 'r') as f:
            entities = json.load(f)
            check_json.check(entities)

        network = Network()
        for entity in entities:
            if entity['type'] == 'host':
                network.add_host(entity['id'])
            if entity['type'] == 'router':
                network.add_router(entity['id'])

        # Links need to be initialized after hosts and routers because Link
        # constructor takes references to hosts/routers
        for entity in entities:
            if entity['type'] == 'link':
                network.add_link(id_=entity['id'],
                                 dev_id_1=entity['endpoints'][0],
                                 dev_id_2=entity['endpoints'][1],
                                 rate=entity['rate'],
                                 delay=entity['delay'],
                                 buf_size=entity['buffer'])
            if entity['type'] == 'flow':
                network.add_flow(id_=entity['id'],
                                 start=entity['start'],
                                 amount=entity['amount'],
                                 src_id=entity['src'],
                                 dst_id=entity['dst'])
        return network
