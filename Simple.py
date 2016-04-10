from address import Address
from sock import Socket
import time


def main():
    port = 30000
    print("Creating socket on port {}".format(port))

    socket = Socket()
    if not socket.open(port):
        print("Failed to open socket")
        return

    while 1:
        data = 'Hello world'

        socket.send(Address(a=127,b=0,c=0,d=1,port=port), data, len(data))

        while 1:
            bytes_read, sender = socket.receive(1024)
            if not bytes_read:
                break

            print(sender)
            print("Received packet from {} ({} bytes)".format(
                sender.address,
                sender.port, bytes_read))

        time.sleep(0.25)
            

if __name__ == '__main__':
    main()
