import socket
from address import Address


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

    def send(self, destination, data, size):
        assert(data)
        assert(size > 0)
        if not self.is_open():
            return False
    
        addr = str(destination.address)
        port = destination.port
    
        data_as_bytes = data.encode('utf-8')

        sent_bytes = 0
        try:
            sent_bytes = self.socket.sendto(data_as_bytes, (addr, port))
        except Exception as e:
            print("Error sending bytes", e)
        finally:
            return sent_bytes == size

    def receive(self, size):
        assert(size > 0)
        
        if self.socket is None:
            return False
        
        try:
            data, addr = self.socket.recvfrom(size)
            if not data or len(addr) < 2:
                return False

            val = socket.inet_aton(addr[0])
            a = int(val[0])
            b = int(val[1])
            c = int(val[2])
            d = int(val[3])

            sender = Address(a=a,b=b,c=c,d=d, port=addr[1])
        except Exception as e:
            data = None
            sender = None

        return data, sender
