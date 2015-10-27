event_manager = None

ACK_SIZE = 64 * 8  # 64 bytes
DATA_PACKET_SIZE = 1024 * 8  # 1024 bytes

# These are heavy-handed simplifications
TIME_BETWEEN_SENDS = 1  # 1 second
TIME_TO_WAIT_UNTIL_ACK = 10  # 10 seconds
