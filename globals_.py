event_manager = None
stats_manager = None

ACK_SIZE = 64 * 8  # 64 bytes
DATA_PACKET_SIZE = 1024 * 8  # 1024 bytes
LINK_MAX_BITS_IN_SEQUENCE = 10 ** 5

# These are heavy-handed simplifications
TIME_BETWEEN_SENDS = 1  # 1 second
TIME_TO_WAIT_UNTIL_ACK = 10  # 10 seconds

DEFAULT_GRAPH_SLIDING_WINDOW_STEP = 0.1  # seconds
DEFAULT_GRAPH_SLIDING_WINDOW_WIDTH = 1  # seconds

SEND_ROUTING_PACKETS_EVERY = 0.2  # seconds
# still magic numbers in Router.initialize_routing_packets_beat

SWITCH_ROUTING_TABLE_EVERY = 5  # seconds
INITIAL_ROUTING_TABLE_SWITCH = 0.4  # seconds

INITIAL_RTT_ESTIMATE = 0.1  # seconds

# interval for increasing window size and
# how long to wait for ack are magic numbers in flow.py
