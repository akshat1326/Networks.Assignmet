# Port numbers used by network layers.
SENDER_PORT = 8080
RECEIVER_PORT = 8081

# Parameters for network.
RTT_MSEC = 100

# Parameters for transport protocols.
TIMEOUT_MSEC = 150

# Packet size for network layer.
MAX_SEGMENT_SIZE = 512
# Packet size for transport layer.
MAX_MESSAGE_SIZE = 500

# Message types used in Transport layer.
MESSAGE_TYPE_DATA = 1
MESSAGE_TYPE_ACK = 2

# Waiting states for the sender in stop and wait
WAIT_FOR_APP_DATA = 1
WAITING_FOR_ACK_MESSAGE = 2