# Usage: python file_receiver.py [dummy|sw|gbn] [file_name]
import config
import functools
import os.path
import sys
import time
import util


def message_handler(file_handler, message):
  print("Received message of length" + str(len(message)))
  file_handler.write(message.decode("utf-8", "ignore"))
    #sys.exit(1)


if __name__ == '__main__':
  if len(sys.argv) != 3:
    print('Usage: python file_receiver.py [sw] [file_name]')
    sys.exit(1)

  transport_layer = None
  transport_layer_name = sys.argv[1]
  file_name = sys.argv[2]
  assert os.path.exists(file_name)
  file_handler = None
  try:
    file_handler = open(file_name, 'w')
    transport_layer = util.get_transport_layer(
        transport_layer_name,
        config.RECEIVER_PORT,
        config.SENDER_PORT,
        functools.partial(message_handler, file_handler))
    while True:
      time.sleep(1)
  finally:
    if file_handler:
      file_handler.close()
    if transport_layer:
      transport_layer.shutdown()