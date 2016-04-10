import socket


class Address(object):
    def __init__(self, address=None, a=None, b=None, c=None, d=None, port=None):
        address = address or 0

        if a is not None:
            self._set_address_from_chars(a,b,c,d)
        else:
            self._set_address_from_int(address)
        
        self._port = port or 0

    def _set_address_from_chars(self, a, b, c, d):
        self._address = (a << 24) | (b << 16) | (c << 8) | d

    def _set_address_from_int(self, address):
        self._address = address

    @property
    def address(self):
        return self._address

    @property
    def port(self):
        return self._port

    @property
    def a(self):
        return self._address >> 24

    @property
    def b(self):
        return self._address >> 16

    @property
    def c(self):
        return self._address >> 8

    @property
    def d(self):
        return self._address

