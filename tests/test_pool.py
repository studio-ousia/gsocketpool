# -*- coding: utf-8 -*-

import gevent

from nose.tools import *
from mock import Mock, patch

from gsocketpool.pool import ConnectionReaper
from gsocketpool.pool import Pool
from gsocketpool.pool import PoolExhaustedError
from gsocketpool.pool import ConnectionNotFoundError


def test_connection_reaper():
    mock_pool = Mock()
    reaper = ConnectionReaper(mock_pool, 0.1)
    reaper.start()

    gevent.sleep(0.5)
    ok_(mock_pool.drop_expired.call_count >= 2)


class TestPool(object):
    def test_create_initial_connections(self):
        mock_factory = Mock()
        pool = Pool(mock_factory, initial_connections=10)

        eq_(10, mock_factory.call_count)
        eq_(10, pool.size)

    @patch('gsocketpool.pool.ConnectionReaper')
    def test_start_connection_reaper(self, mock_reaper):
        mock_reaper_ins = Mock()
        mock_reaper.return_value = mock_reaper_ins

        pool = Pool(Mock(), reap_expired_connections=True, reap_interval=3)

        mock_reaper.assert_called_once_with(pool, 3)
        mock_reaper_ins.start.assert_called_once_with()

    def test_connection_context_manager(self):
        mock_factory = Mock()
        mock_connection = Mock()
        mock_factory.return_value = mock_connection

        pool = Pool(mock_factory)

        with pool.connection() as conn:
            eq_(mock_connection, conn)
            ok_(mock_connection in pool._using)

        ok_(not mock_connection in pool._using)
        ok_(mock_connection in pool._pool)

    def test_acquire_and_release(self):
        mock_factory = Mock()
        mock_conn1 = Mock()
        mock_conn2 = Mock()
        mock_factory.side_effect = [mock_conn1, mock_conn2]
        pool = Pool(mock_factory, initial_connections=0)

        eq_(0, pool.size)

        # acquire conn1
        conn1 = pool.acquire()
        eq_(mock_conn1, conn1)
        eq_(1, pool.size)
        ok_(conn1 not in pool._pool)
        ok_(conn1 in pool._using)

        # acquire conn2
        conn2 = pool.acquire()
        eq_(mock_conn2, conn2)
        eq_(2, pool.size)
        ok_(conn2 in pool._using)

        # release conn1
        pool.release(conn1)
        ok_(conn1 in pool._pool)
        ok_(conn1 not in pool._using)

        # acquire conn1 again
        conn1_2 = pool.acquire()
        eq_(mock_conn1, conn1_2)
        eq_(2, pool.size)
        ok_(conn1_2 not in pool._pool)
        ok_(conn1_2 in pool._using)

        # release conn2
        pool.release(conn2)
        ok_(conn2 in pool._pool)
        ok_(conn2 not in pool._using)

        # release conn1
        pool.release(conn1_2)
        ok_(conn1_2 in pool._pool)
        ok_(conn1_2 not in pool._using)

    def test_acquire_retry(self):
        pool = Pool(Mock(), max_connections=1)
        conn1 = pool.acquire()  # make the pool reach the max connection

        gevent.spawn_later(0, pool.release, conn1)
        conn = pool.acquire(retry=1)
        eq_(conn, conn1)

    @raises(PoolExhaustedError)
    def test_acquire_disable_retry(self):
        pool = Pool(Mock(), max_connections=1)
        conn1 = pool.acquire()  # make the pool reach the max connection

        gevent.spawn_later(0, pool.release, conn1)
        pool.acquire(retry=0)

    @raises(ConnectionNotFoundError)
    def test_release_invalid_connection(self):
        pool = Pool(Mock())

        pool.release(Mock())

    @raises(ConnectionNotFoundError)
    def test_release_already_released_connection(self):
        pool = Pool(Mock())
        conn1 = pool.acquire()

        pool.release(conn1)
        pool.release(conn1)

    @raises(PoolExhaustedError)
    def test_max_connections(self):
        pool = Pool(Mock(), max_connections=1)
        for _ in range(2):
            pool.acquire()

    def test_drop(self):
        pool = Pool(Mock())
        conn1 = pool.acquire()
        pool.release(conn1)

        ok_(conn1 in pool._pool)

        pool.drop(conn1)

        ok_(conn1 not in pool._pool)
        conn1.close.assert_called_once_with()

    def test_drop_closed_connection(self):
        pool = Pool(Mock())
        conn1 = pool.acquire()
        conn1.is_connected = Mock()
        conn1.is_connected.return_value = False
        pool.release(conn1)

        ok_(conn1 in pool._pool)

        pool.drop(conn1)

        ok_(conn1 not in pool._pool)
        ok_(not conn1.close.called)

    @raises(ConnectionNotFoundError)
    def test_drop_using_connection(self):
        pool = Pool(Mock())

        conn1 = pool.acquire()
        pool.drop(conn1)

    @raises(ConnectionNotFoundError)
    def test_drop_invalid_connection(self):
        pool = Pool(Mock())

        pool.drop(Mock())

    def test_drop_expired_connections(self):
        mock_factory = Mock()

        mock_conn1 = Mock()
        mock_conn2 = Mock()
        mock_conn3 = Mock()

        mock_conn1.is_expired.return_value = True
        mock_conn2.is_expired.return_value = False
        mock_conn3.is_expired.return_value = True

        mock_factory.side_effect = [mock_conn1, mock_conn2, mock_conn3]
        pool = Pool(mock_factory, initial_connections=3)

        pool.drop_expired()

        ok_(mock_conn1 not in pool._pool)
        mock_conn1.close.assert_called_once_with()
        ok_(mock_conn2 in pool._pool)
        ok_(mock_conn3 not in pool._pool)
        mock_conn1.close.assert_called_once_with()
