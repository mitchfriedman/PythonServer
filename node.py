import re
from address import Address
from sock import Socket
import time


def main():
    port = 30000
    print("Creating socket on port {}".format(port))
    socket = Socket()

    if not socket.open(port):
        print("Failed to create socket")
        return

    addresses = get_addresses_from_file('addresses.txt')

    while 1:
        data = 'Hello world'
        for address in addresses:
            socket.send(address, data, len(data))

        while 1:
            bytes_read, sender = socket.receive(1024)
            if not bytes_read:
                break
            print("Received packet from {}.{}.{}.{} ({} bytes)".format(
                sender.a, sender.b, sender.c, sender.d, len(bytes_read)))

        time.sleep(0.5)
    

def get_addresses_from_file(file_name):
    addresses = []
    with open(file_name, "r") as fp:
        for line in fp.readlines():
            ip = re.search(r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}:[0-9]{1,6}$', line, re.M|re.I)
            if ip:
                ip = ip.group()
                a,b,c,d_and_port= ip.split('.')
                d, port = d_and_port.split(':')
                addresses.append(Address(a=int(a),b=int(b),c=int(c),d=int(d),port=int(port)))

    return addresses

if __name__ == "__main__":
    main()
