import socket
from address import Address
import sys
import pickle
import io


class Socket(object):
    def __init__(self):
        self.socket = None

    def open(self, port):
        assert(not self.is_open())
        host = '127.0.0.1'#socket.gethostname()
        
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setblocking(0)
        except Exception as e:
            print("Error creating socket", e)
            return False
    
        try:
            self.socket.bind((host, port))
            #self.socket.listen(0)
        except Exception as e:
            print("Error binding socket", e)
            return False

        return True

    def is_open(self):
        return self.socket is not None

    def close(self):
        if socket is not None:
            self.socket.close()

    def send(self, destination, data):
        assert(data)
        if not self.is_open():
            return False
    
        addr = str(destination.address)
        port = destination.port
    
        with open('serialize.txt', 'wb') as f:
            pickle.dump(data, f)

        contents = open('serialize.txt', 'rb').read()

        try:
            sent_bytes = self.socket.sendto(contents, (addr, port))
            return True
        except Exception as e:
            print("Error sending bytes", e)
            return False

    def receive(self, size):
        assert(size > 0)
        
        if self.socket is None:
            return False
        
        try:
            data, addr = self.socket.recvfrom(size)
            if not data or len(addr) < 2:
                return False
            
            with open('contents.txt', 'wb') as f:
                f.write(data)

            with open('contents.txt', 'rb') as f:
                deserialized = pickle.load(f)

            val = socket.inet_aton(addr[0])
            a = int(val[0])
            b = int(val[1])
            c = int(val[2])
            d = int(val[3])

            sender = Address(a=a,b=b,c=c,d=d, port=addr[1])
        except Exception as e:
            deserialized = None
            sender = None

        return deserialized, sender
