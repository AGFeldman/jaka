import random


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

    def register_network(self, network):
        self.set_actors(network.get_actors())
        self.set_flows(network.get_flows())
        for flow in self.flows:
            flow.schedule_with_event_manager()

    def set_actors(self, actors):
        self.actors = actors

    def set_flows(self, flows):
        self.flows = flows

    def get_time(self):
        return self.time

    def add(self, time_until_action, action):
        assert time_until_action >= 0
        self.queue.append((self.get_time() + time_until_action, action))
        self.queue.sort()

    def add_eternal(self, time_until_action, action):
        assert time_until_action >= 0
        self.eternal_queue.append((self.get_time() + time_until_action, action))
        self.eternal_queue.sort()

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

            if all((flow.finished for flow in self.flows)):
                break
