# -*- coding: utf-8 -*-

import time
import logging
from gevent import socket


class Connection(object):
    """A base connection class.

    Arbitrary connections can be defined by extending this class.
    """

    def open(self):
        """Opens a connection."""

        raise NotImplementedError()

    def close(self):
        """Closes the connection."""

        raise NotImplementedError()

    def get(self):
        """Returns the raw connection."""
        raise NotImplementedError()

    def is_connected(self):
        """Returns whether the connection has been established.

        :rtype: bool
        """
        raise NotImplementedError()

    def is_expired(self):
        """Returns whether the connection is expired.

        :rtype: bool
        """
        return False

    def reconnect(self):
        """Attempts to reconnect the connection."""

        try:
            if self.is_connected():
                self.close()
            self.open()
        except:
            logging.exception('Failed to reconnect')


class TcpConnection(Connection):
    """A TCP connection.

    :param str host: Hostname.
    :param int port: Port.
    :param int lifetime: Maximum lifetime (in seconds) of the connection.
    :param int timeout: Socket timeout.
    """

    def __init__(self, host, port, lifetime=600, timeout=None):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._host = host
        self._port = port
        self._lifetime = lifetime
        self._timeout = timeout
        self._connected = False
        self._created = None

    @property
    def socket(self):
        return self._sock

    def get(self):
        return self._sock

    def open(self):
        self._sock.connect((self._host, self._port))
        if self._timeout:
            self._sock.settimeout(self._timeout)

        self._connected = True
        self._created = time.time()

    def close(self):
        if self._connected:
            self._sock.close()
            self._connected = False

    def is_connected(self):
        return self._connected

    def is_expired(self):
        if time.time() - self._created > self._lifetime:
            return True
        else:
            return False

    def send(self, data):
        assert self._connected

        self._sock.send(data)

    def recv(self, size=1024):
        assert self._connected

        return self._sock.recv(size)
