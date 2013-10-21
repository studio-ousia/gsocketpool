Introduction
============

gsocketpool is a simple connection pool for gevent.

Basic Usage
-----------

The following is an example to create a connection pool that communicates an echo server running on *localhost 2000*.

.. code-block:: python

    >>> from gsocketpool import Pool
    >>> from gsocketpool import TcpConnection
    >>> 
    >>> options = dict(host='localhost', port=2000)
    >>> pool = Pool(TcpConnection, options)
    >>> 
    >>> with pool.connection() as conn:
    ...     conn.send('hello')
    ...     print conn.recv()
    hello


Implementing Protocol
---------------------

Arbitrary protocols can be easily implemented by extending :class:`Connection <gsocketpool.connection.Connection>` class. You have to override at least three functions such as :func:`open() <gsocketpool.connection.Connection.open>`, :func:`close() <gsocketpool.connection.Connection.close>` and :func:`is_connected() <gsocketpool.connection.Connection.is_connected>`.


:class:`TcpConnection <gsocketpool.connection.TcpConnection>` used in the above example is also implemented as a subclass of :class:`Connection <gsocketpool.connection.Connection>`.


.. code-block:: python

    class TcpConnection(Connection):

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

For detailed usage, please refer to the :doc:`API reference <api>`.
