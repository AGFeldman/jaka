from __future__ import division


event_manager = None
stats_manager = None

ACK_SIZE = 64 * 8  # 64 bytes
DATA_PACKET_SIZE = 1024 * 8  # 1024 bytes
LINK_MAX_BITS_IN_SEQUENCE = 10 ** 6

DEFAULT_GRAPH_SLIDING_WINDOW_STEP = 0.1  # seconds
DEFAULT_GRAPH_SLIDING_WINDOW_WIDTH = 1  # seconds

SEND_ROUTING_PACKETS_EVERY = 0.2  # seconds
# still magic numbers in Router.initialize_routing_packets_beat

SWITCH_ROUTING_TABLE_EVERY = 5  # seconds
INITIAL_ROUTING_TABLE_SWITCH = 0.4  # seconds

INITIAL_RTT_ESTIMATE = 0.1  # seconds
# Use the last NUM_OBSERVATIONS_FOR_RTTE observations when estimating average RTT
# We choose this number such that if a flow transmits at 10 Mbps, then we
# consider round trip time observations made in the last ~1 second
# TODO(agf): Calibrate
NUM_OBSERVATIONS_FOR_RTTE = int(1 * 10 * 10 ** 6 / DATA_PACKET_SIZE)

# interval for increasing window size and
# how long to wait for ack are magic numbers in flow.py
