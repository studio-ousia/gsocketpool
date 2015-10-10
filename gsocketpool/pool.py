# -*- coding: utf-8 -*-

from __future__ import absolute_import

import collections
import logging
import contextlib
import gevent
from gevent import Greenlet

from gsocketpool.exceptions import ConnectionNotFoundError, PoolExhaustedError


class ConnectionReaper(Greenlet):
    def __init__(self, pool, interval=180):
        self._pool = pool
        self._delay = interval
        Greenlet.__init__(self)

    def _run(self):
        while True:
            gevent.sleep(self._delay)
            try:
                self._pool.drop_expired()
            except:
                logging.exception('An error has occurred while dropping expired connections')


class Pool(object):
    """Connection pool.

    Usage:
        Communicating echo server running on localhost 2000:

        >>> 
        >>> from gsocketpool import Pool
        >>> from gsocketpool import TcpConnection
        >>> options = dict(host='localhost', port=2000)
        >>> pool = Pool(TcpConnection, options)
        >>> 
        >>> with pool.connection() as conn:
        ...     conn.send('hello')
        ...     print conn.recv()
        hello

    :param factory: :class:`Connection <gsocketpool.connection.Connection>`
        class or a callable that creates
        :class:`Connection <gsocketpool.connection.Connection>` instance.
    :param dict options: (optional) Options to pass to the factory.
    :param int initial_connections: (optional) The number of connections that
        are initially established.
    :param int max_connections: (optional) The maximum number of connections.
    :param bool reap_expired_connections: (optional) If set to True, a
        background thread (greenlet) that periodically kills expired connections
        will be launched.
    :param int reap_interval: (optional) The interval to run to kill expired
        connections.
    """

    def __init__(self, factory, options={}, initial_connections=0,
                 max_connections=200, reap_expired_connections=True,
                 reap_interval=180):

        self._factory = factory
        self._options = options
        self._max_connections = max_connections

        self._pool = collections.deque()
        self._using = collections.deque()

        assert initial_connections <= max_connections, "initial_connections must be less than max_connections"

        for i in range(initial_connections):
            self._pool.append(self._create_connection())

        if reap_expired_connections:
            self._reaper = ConnectionReaper(self, reap_interval)
            self._reaper.start()

    def __del__(self):
        for conn in self._pool:
            conn.close()
        self._pool = None

        for conn in self._using:
            conn.close()
        self._using = None

    @contextlib.contextmanager
    def connection(self):
        conn = self.acquire()
        try:
            yield conn

        finally:
            self.release(conn)

    @property
    def size(self):
        """Returns the pool size."""

        return len(self._pool) + len(self._using)

    def acquire(self, retry=10, retried=0):
        """Acquires a connection from the pool.

        :param int retry: (optional) The maximum number of times to retry.
        :returns: :class:`Connection <gsocketpool.connection.Connection>` instance.
        :raises:  :class:`PoolExhaustedError <gsocketpool.exceptions.PoolExhaustedError>`
        """

        if len(self._pool):
            conn = self._pool.popleft()
            self._using.append(conn)

            return conn

        else:
            if len(self._pool) + len(self._using) < self._max_connections:
                conn = self._create_connection()
                self._using.append(conn)
                return conn

            else:
                if retried >= retry:
                    raise PoolExhaustedError()
                retried += 1

                gevent.sleep(0.1)

                return self.acquire(retry=retry, retried=retried)

    def release(self, conn):
        """Releases the connection.

        :param Connection conn: :class:`Connection <gsocketpool.connection.Connection>` instance.
        :raises: :class:`ConnectionNotFoundError <gsocketpool.exceptions.ConnectionNotFoundError>`
        """

        if conn in self._using:
            self._using.remove(conn)
            self._pool.append(conn)

        else:
            raise ConnectionNotFoundError()

    def drop(self, conn):
        """Removes the connection from the pool.

        :param Connection conn: :class:`Connection <gsocketpool.connection.Connection>` instance.
        :raises: :class:`ConnectionNotFoundError <gsocketpool.exceptions.ConnectionNotFoundError>`
        """

        if conn in self._pool:
            self._pool.remove(conn)
            if conn.is_connected():
                conn.close()

        else:
            raise ConnectionNotFoundError()

    def drop_expired(self):
        """Removes all expired connections from the pool.

        :param Connection conn: :class:`Connection <gsocketpool.connection.Connection>` instance.
        """

        expired_conns = [conn for conn in self._pool if conn.is_expired()]

        for conn in expired_conns:
            self.drop(conn)

    def _create_connection(self):
        conn = self._factory(**self._options)
        conn.open()

        return conn
