import heapq
import signal


class EventManager(object):
    '''
    Intended as singleton class
    One important field is self.actors. After each event is processed,
    EventManager calls the act() method on each actor in self.actors. It
    continues calling the act() method on each actor until no actors wish to
    act -- that is, until all act() calls return false.
    self.queue is maintained as a heapq of (time_of_exection, function,
    description) elements.
    '''

    def __init__(self, output_name):
        '''
        Usage warning: If |output_name| is None, then a call to self.log() will
        break things.
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
        # any stuff like routing tables. Current code might not take advantage
        # of this.
        def no_op():
            pass
        self.add(0, no_op)

    def log(self, msg):
        '''
        Write a line to the log file.
        This will break if constructor was called with output_name=None.
        '''
        with open(self.output_name, 'a') as f:
            f.write('Time {} : {}\n'.format(self.get_time(), msg))

    def register_network(self, network):
        '''
        Processes a Network object
        '''
        self.actors = network.get_actors()
        for actor in self.actors:
            if hasattr(actor, 'register_with_event_manager'):
                actor.register_with_event_manager()

        self.flows = network.get_flows()

        # Handle SIGINT / when the user presses control-C by stopping the
        # simulation, but not exiting. This allows us to still output graphs.
        def sigint_handler(signal, frame):
            self.log("Received SIGINT, stopping simulation")
            for flow in self.flows:
                flow.finished = True
        signal.signal(signal.SIGINT, sigint_handler)

    def get_time(self):
        return self.time

    def add(self, time_until_action, action):
        '''
        Add an action to the event queue
        |time_until_action| should be a float
        |action| should be callable
        '''
        assert time_until_action >= 0
        heapq.heappush(self.queue, (self.get_time() + time_until_action, action))

    def run(self):
        '''
        Start the event processing loop
        '''
        while self.queue:
            self.time, scheduled_action = heapq.heappop(self.queue)
            scheduled_action()

            # Now we handle instantaneous actions.
            # One actor acting could cause another actor to want to act, so
            # we loop until all no actors wish to act.
            keep_acting = True
            while keep_acting:
                keep_acting = False
                for actor in self.actors:
                    if actor.act():
                        keep_acting = True

            # It is necessary to exit the loop if all flows are finished.
            # Otherwise, the loop will continue processing perpetual events
            # such as routing packet sends.
            if all((flow.finished for flow in self.flows)):
                break
