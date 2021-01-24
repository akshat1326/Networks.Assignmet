import collections
import config
import random
import socket
import threading
import time


class NetworkLayer:
  def __init__(self, send_port, receive_port, transport_layer):
    # Port for receiving and sending packets.
    self.send_port = send_port
    self.receive_port = receive_port
    # Listening on send_port to recv packets.
    self.soc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    self.soc.bind(('localhost', send_port))
    self.soc.settimeout(0.5)  # seconds.
    # Hold transport layer object for message demultiplexing.
    self.transport_layer = transport_layer
    # Buffer for holding messages to be delivered to transport layer.
    self.message_buffer = collections.deque(maxlen=8)
    self.buffer_lock = threading.Lock()
    # Start reading network packet thread.
    self.stop_accept_pkt = False
    threading.Thread(target=self._packet_reader).start()


  def shutdown(self):
    self.stop_accept_pkt = True


  ## message should be of type bytes, not string.
  def send(self, message):
    self.soc.sendto(message, ('localhost', self.receive_port))


  def recv(self):
    message = ''
    with self.buffer_lock:
      if len(self.message_buffer) > 0:
        message = self.message_buffer.popleft()
    return message


  def _packet_reader(self):
    while not self.stop_accept_pkt:
      # If message is  received, notify the transport layer instead of blocking reading.
      has_message = False
      with self.buffer_lock:
        if len(self.message_buffer) > 0:
          has_message = True
      if has_message:
        self.transport_layer.handle_arrival_msg()
        continue
      try:
        msg, addr = self.soc.recvfrom(config.MAX_SEGMENT_SIZE)
        with self.buffer_lock:
          if len(self.message_buffer) < self.message_buffer.maxlen:
            self.message_buffer.append(msg)
      except socket.timeout:
        # If timeout happens, then just continue.
        pass


