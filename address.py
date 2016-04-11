class Address(object):
    def __init__(self, a=None, b=None, c=None, d=None, port=None):
        self.a = a
        self.b = b
        self.c = c
        self.d = d
        
        if self.a:
            self._address = (a << 24) | (b << 16) | (c << 8) | d
        else:
            self._address = 0

        self._port = port or 0

    @property
    def address(self):
        return self._address

    @property
    def port(self):
        return self._port

    def __eq__(self, other):
        return self.address == other.address
