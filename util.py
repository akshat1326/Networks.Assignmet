import ss
import struct
import time

SIXTEEN_BIT_MASK = 0xffff

# A class to wrap various pieces of information included in a transport layer segment which includes
#  the type of message (ACK or DATA), the sequence number, the checksum value, and the messagetext. In
# addition, it contains a boolean flag indicating the presence of data corruption.
class RDTPacket:
  def __init__(self, message_type, sequence_number, checksum, messagetext, is_corrupt):
    self.message_type = message_type
    self.sequence_number = sequence_number
    self.checksum = checksum
    self.messagetext = messagetext
    self.is_corrupt = is_corrupt


def get_corrupt_packet_representation():
  return RDTPacket(None, None, None, None, True)


def get_checksum(pkt):
  checksum = 0
  byte_list = list(pkt[i:i+2] for i in range(0, len(pkt), 2))
  for chunk in byte_list:
    num = struct.unpack('!H', chunk)[0] if len(chunk) == 2 else struct.unpack('!B', chunk)[0]
    checksum += num
  # fold the carry so the checksum is 16 bits long
  checksum = (checksum >> 16) + (checksum & SIXTEEN_BIT_MASK)
  return checksum ^ SIXTEEN_BIT_MASK   # get one's complement


def make_packet(message, type, sequence_number):
  msglist = []
  msglist.append(struct.pack('!H', type))                 # HEADER 1: MESSAGE TYPE
  msglist.append(struct.pack('!H', sequence_number))      # HEADER 2: SEQUENCE NUMBER
  msglist.append(struct.pack('!H', 0))                    # HEADER 3: CHECKSUM (append 0 for now)
  msglist.append(message)                                 # The messagetext

  checksum = get_checksum(b''.join(msglist))
  checksum_bytes = struct.pack("!H", checksum)
  assert len(checksum_bytes) == 2

  msglist[2] = checksum_bytes
  packet = b''.join(msglist)
  return packet


def extract_data(message):
  if len(message) < 6 or not get_checksum(message) == 0:
    return get_corrupt_packet_representation()
  headers = struct.unpack("!3H", message[0:6])
  return RDTPacket(headers[0], headers[1], headers[2], message[6:], False)


def packet_to_string(packet):
  type = "type: " + ("ACK" if packet.message_type == 2 else "DATA")
  sequence_number = "sequence_number: " + str(packet.sequence_number)
  messagetext = ""
  if(packet.messagetext):
    messagetext = ", messagetext: " + str(packet.messagetext)[:20]
    if len(packet.messagetext) > 20: messagetext += "..."
  return " [" + type + ", " + sequence_number + messagetext + "]"


def get_transport_layer(name, send_port, receive_port, message_handler):
  assert name == 'sw'
  if name == 'sw':
    return ss.StopAndWait(send_port, receive_port, message_handler)


def now():
  return time.strftime("[%a %m-%d-%y %H:%M:%S] ")


def log(msg):
  #file_handler = open("log.txt", 'a')
  #file_handler.write((now() + msg))
  print(now() + msg)