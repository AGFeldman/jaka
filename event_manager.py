import random
import heapq


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

    def __init__(self, output_name):
        '''
        If |output_name| is None, then we should never call self.log()
        '''
        self.flows = dict()
        self.actors = []

        if output_name is not None:
            self.output_name = output_name + '.log'
            # Clear the contents of the file self.output_name
            with open(self.output_name, 'w') as f:
                f.write('')

        # Use heapq.heappush(self.queue, ...) and heapq.heappop(self.queue)
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
        '''
        Will break if constructor was called with output_name=None
        '''
        with open(self.output_name, 'a') as f:
            f.write('Time {} : {}\n'.format(self.get_time(), msg))

    def register_network(self, network):
        self.actors = network.get_actors()
        for actor in self.actors:
            # TODO(agf): Make this more tolerant of mis-spellings. Seriously.
            if hasattr(actor, 'register_with_event_manager'):
                actor.register_with_event_manager()

        self.flows = network.get_flows()

    def get_time(self):
        return self.time

    def add(self, time_until_action, action):
        assert time_until_action >= 0
        heapq.heappush(self.queue, (self.get_time() + time_until_action, action))

    def run(self):
        while self.queue:
            self.time, scheduled_action = heapq.heappop(self.queue)
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

            if all((flow.finished for flow in self.flows)):
                break
