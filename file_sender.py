# Usage: python file_sender.py [dummy|sw|gbn] [file_name]
import config
import os.path
import sys
import time
import util


if __name__ == '__main__':
  if len(sys.argv) != 3:
    print('Usage: python file_sender.py [sw] [file_name]')
    sys.exit(1)

  transport_layer = None
  transport_layer_name = sys.argv[1]
  file_name = sys.argv[2]
  assert os.path.isfile(file_name)
  start_time = time.time()
  try:
    transport_layer = util.get_transport_layer(
        transport_layer_name,
        config.SENDER_PORT,
        config.RECEIVER_PORT, None)
    with open(file_name, 'rb') as f:
      while True:
        msg = f.read(config.MAX_MESSAGE_SIZE)
        if not msg: break
        print('Message of length ' + str(len(msg)))
        while not transport_layer.send(msg):
          pass
  finally:
    if transport_layer:
      transport_layer.shutdown()
    end_time = time.time()
    print('Time used [secs]:', end_time - start_time)
    file_handler = open("timelog.txt", 'a')
    file_handler.write(str(end_time - start_time))
    file_handler.write("\n")