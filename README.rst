gsocketpool
===========

A simple connection pool for gevent.

.. code-block:: python

    >>> from gsocketpool.pool import Pool
    >>> from gsocketpool.connection import TcpConnection
    >>> 
    >>> options = dict(host='localhost', port=2000)
    >>> pool = Pool(TcpConnection, options)
    >>> 
    >>> with pool.connection() as conn:
    ...     conn.send('hello')
    ...     print conn.recv()
    hello
