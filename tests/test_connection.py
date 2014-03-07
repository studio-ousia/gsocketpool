# -*- coding: utf-8 -*-

import time
from gevent import socket

from mock import Mock, patch
from nose.tools import *

from gsocketpool.connection import Connection
from gsocketpool.connection import TcpConnection


class TestConnection(object):
    def test_reconnect(self):
        conn = Connection()

        conn.open = Mock()
        conn.close = Mock()
        conn.is_connected = Mock()
        conn.is_connected.return_value = True

        conn.reconnect()
        conn.close.assert_called_once_with()
        conn.open.assert_called_once_with()

    def test_reconnect_not_connected(self):
        conn = Connection()

        conn.open = Mock()
        conn.close = Mock()
        conn.is_connected = Mock()
        conn.is_connected.return_value = False

        conn.reconnect()
        ok_(not conn.close.called)
        conn.open.assert_called_once_with()


class TestTcpConnection(object):
    @patch('gevent.socket.socket')
    def test_socket_creation(self, mock_socket):
        TcpConnection('localhost', 2000)

        mock_socket.assert_called_once_with(socket.AF_INET, socket.SOCK_STREAM)

    @patch('gevent.socket.socket')
    def test_open(self, mock_socket):
        conn = TcpConnection('localhost', 2000)
        conn.open()
        conn.get().connect.assert_called_once_with(('localhost', 2000))

        ok_(conn.is_connected())

    @patch('gevent.socket.socket')
    def test_open_with_timeout(self, mock_socket):
        conn = TcpConnection('localhost', 2000, timeout=10)
        conn.open()

        conn.get().settimeout.assert_called_once_with(10)

    @patch('gevent.socket.socket')
    def test_close(self, mock_socket):
        conn = TcpConnection('localhost', 2000)
        conn.open()
        conn.close()

        conn.get().close.assert_called_once_with()
        ok_(not conn.is_connected())

    @patch('gevent.socket.socket')
    def test_is_expired(self, mock_socket):
        conn = TcpConnection('localhost', 2000, lifetime=1)
        conn.open()

        ok_(not conn.is_expired())
        time.sleep(1)
        ok_(conn.is_expired())

    @patch('gevent.socket.socket')
    def test_send(self, mock_socket):
        conn = TcpConnection('localhost', 2000)
        conn.open()

        conn.send('dummy')
        conn.get().send.assert_called_once_with('dummy')

    @patch('gevent.socket.socket')
    def test_recv(self, mock_socket):
        conn = TcpConnection('localhost', 2000)
        conn.open()

        conn.recv(20)
        conn.get().recv.assert_called_once_with(20)
