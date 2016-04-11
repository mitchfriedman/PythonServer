from address import Address
from sock import Socket


class Connection(object):
    State = {
        'Disconnected': 0,
        'Listening': 1,
        'Connecting': 2,
        'ConnectFail': 3,
        'Connected': 4,
    }

    Mode = {
        'Client': 1,
        'Server': 2,
    }

    def __init__(self, protocol_id, timeout):
        self._protocol_id = protocol_id
        self._timeout = timeout

        self._mode = None
        self.running = False

        self.state = None
        self.socket = Socket()
        self.address = Address()
        self.timeout_accumulator = 0

        self.local_sequence_number = 0

        self.clear_data()

    def start(self, port):
        assert (not self.running)
        print("Starting connection on port {}".format(port))
        if not self.socket.open(port):
            return False

        self.running = True
        return True

    def stop(self):
        assert self.running
        print("Stop connection")
        self.clear_data()
        self.socket.close()
        self.running = False

    def listen(self):
        print("Server listening for connection")
        self.clear_data()
        self._mode = self.Mode['Server']
        self.state = self.State['Listening']

    def connect(self, address):
        print("client connection to {}.{}.{}.{}:{}".format(address.a, address.b, address.c, address.d, address.port))
        self.clear_data()
        self._mode = self.Mode['Client']
        self.state = self.State['Connecting']
        self.address = address

    def is_connecting(self):
        return self.state == self.State['Connecting']

    def connect_failed(self):
        return self.state == self.State['ConnectFail']

    def is_connected(self):
        return self.state == self.State['Connected']

    def is_listening(self):
        return self.state == self.State['Listening']

    @property
    def mode(self):
        return self._mode

    def update(self, delta_time):
        assert self.running
        self.timeout_accumulator += delta_time
        if self.timeout_accumulator > self._timeout:
            if self.state == self.State['Connecting']:
                print("Connection timed out")
                self.clear_data()
                self.state = self.State['ConnectFail']
            elif self.state == self.State['Connected']:
                print("Connection timed out")
                self.clear_data()
                if self.state == self.State['Connecting']:
                    self.state = self.State['ConnectFail']

    def send_packet(self, data):
        assert self.running
        if self.address.address == 0:
            return False
        packet = [0] * (4 + len(data))
        packet[0] = self._protocol_id >> 24
        packet[1] = (self._protocol_id >> 16) & 0xFF
        packet[2] = (self._protocol_id >> 8) & 0xFF
        packet[3] = self._protocol_id & 0xFF
        packet[4:] = data[:]

        return self.socket.send(self.address, packet), packet

    def receive_packet(self, size):
        assert self.running

        bytes_read, sender = self.socket.receive(size + 4)

        if not bytes_read or len(bytes_read) <= 4:
            return 0, []

        if (bytes_read[0] != self._protocol_id >> 24 or
                    bytes_read[1] != ((self._protocol_id >> 16) & 0xFF) or
                    bytes_read[2] != ((self._protocol_id >> 8) & 0xFF) or
                    bytes_read[3] != (self._protocol_id & 0xFF)):
            return 0, []

        if self._mode == self.Mode['Server'] and not self.is_connected():
            print("Server accepts connection from client {}:{}".format(sender.address, sender.port))
            self.state = self.State['Connected']
            self.address = sender

        if sender == self.address:
            if self._mode == self.Mode['Client'] and self.state == self.State['Connecting']:
                print("Client completes connection with server")
                self.state = self.State['Connected']

            self.timeout_accumulator = 0
            return size - 4, bytes_read[4:]

        return 0, []

    def clear_data(self):
        self.state = self.State['Disconnected']
        self.timeout_accumulator = 0
        self.address = Address()

        self.local_sequence_number = 0
