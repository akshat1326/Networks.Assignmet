import config
import threading
import time
import udt
import sys
import util

# Stop-And-Wait reliable transport protocol.
class StopAndWait:

  # "message_handler" is used to deliver messages to application layer
  def __init__(self, local_port, remote_port, message_handler):
    util.log("Starting up Stop and Wait protocol ... ")
    self.network_layer = udt.NetworkLayer(local_port, remote_port, self)
    self.message_handler = message_handler
    self.sequence_number = 0
    self.last_pkt_sent = b''
    self.last_packet_sent_data = None
    self.sender_lock = threading.Lock()
    self.sender_state = config.WAIT_FOR_APP_DATA
    self.set_timer()
    self.is_receiver = True


  def set_timer(self):
    self.timer = threading.Timer((config.TIMEOUT_MSEC/1000.0), self.timeout)


  # "send" is called by application. Return true on success, false otherwise.
  def send(self, msg):
    self.is_receiver = False
    util.log("Called by app to send following message: <" + str(msg)[:20] + "...>")
    threading.Thread(target=self.send_helper(msg))
    return True


  # Helper fn for thread to handle waiting for ACK before sending next piece of data
  def send_helper(self ,msg):
    while self.sender_state == config.WAITING_FOR_ACK_MESSAGE:
      # sleep here so less busy waiting.
      time.sleep(0.01)
    packet = util.make_packet(msg, config.MESSAGE_TYPE_DATA, self.sequence_number)
    packet_data = util.extract_data(packet)
    self.sender_lock.acquire()
    util.log("Sending data: " + util.packet_to_string(packet_data))
    self.network_layer.send(packet)
    self.last_pkt_sent = packet
    self.last_packet_sent_data = packet_data
    self.sender_state = config.WAITING_FOR_ACK_MESSAGE 
    self.set_timer()
    self.timer.start()
    self.sender_lock.release()
    return


  # "handler" to be called by network layer when packet is ready. from BELOW
  def handle_arrival_msg(self):
    message = self.network_layer.recv()
    message_data = util.extract_data(message)

    if(message_data.is_corrupt):
      if(self.is_receiver):
        if not self.last_packet_sent_data: return
        util.log("Received corrupt data. Resending: " + util.packet_to_string(self.last_packet_sent_data))
        self.network_layer.send(self.last_pkt_sent)
      return

    # If ACK message, assume its for sender
    if message_data.message_type == config.MESSAGE_TYPE_ACK:
      if self.sender_state == config.WAITING_FOR_ACK_MESSAGE and message_data.sequence_number == self.sequence_number:
        util.log("Received ACK with expected sequence #. " + util.packet_to_string(message_data))
        self.sender_lock.acquire()
        self.timer.cancel()
        self.sequence_number = not (self.sequence_number)  # flip the sequence number
        self.sender_state = config.WAIT_FOR_APP_DATA
        self.sender_lock.release()
    # If DATA message, assume its for receiver
    else:
      assert message_data.message_type == config.MESSAGE_TYPE_DATA
      util.log("Received DATA: " + util.packet_to_string(message_data))
      if message_data.sequence_number == self.sequence_number:
        self.message_handler(message_data.messagetext)
        ack_pkt = util.make_packet(b'', config.MESSAGE_TYPE_ACK, self.sequence_number)
        self.network_layer.send(ack_pkt)
        self.last_pkt_sent = ack_pkt
        self.last_packet_sent_data = util.extract_data(ack_pkt)
        self.sequence_number = not (self.sequence_number)  # flip the sequence number
        util.log("Sent ACK: " + util.packet_to_string(self.last_packet_sent_data))
        
      else:
        util.log("Duplicate DATA message. Resending ACK message with sequence # "
              + str(int(self.last_packet_sent_data.sequence_number)) + ".")
        self.network_layer.send(self.last_pkt_sent)
    return


  # Cleanup resources.
  def shutdown(self):
    if not self.is_receiver: self._wait_for_last_ACK()
    if self.timer.is_alive(): self.timer.cancel()
    util.log("Connection shutting down...")
    self.network_layer.shutdown()


  def _wait_for_last_ACK(self):
    while self.sender_state == config.WAITING_FOR_ACK_MESSAGE:
      util.log("Waiting for last ACK from receiver with sequence # " + str(int(self.sequence_number)) + ".")
      time.sleep(1)


  def timeout(self):
    util.log("Timeout! Resend last packet: " + util.packet_to_string(self.last_packet_sent_data))
    self.sender_lock.acquire()
    self.network_layer.send(self.last_pkt_sent)
    self.set_timer()
    self.sender_lock.release()
    self.timer.start()
    return