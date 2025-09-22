# coding=utf-8
#
# Copyright (C) 2018-2025 by dream-alpha
#
# In case of reuse of this source code please do not remove this copyright.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# For more information on the GNU General Public License see:
# <http://www.gnu.org/licenses/>.


import socket
import json
import threading
import time
from twisted.internet import reactor
from .UnicodeUtils import convertUni2Str
from .Debug import logger


class SocketClient(object):
    def __init__(self, host='127.0.0.1', port=5000, timeout=5, on_message=None):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.sock = None
        self._thread = None
        self._running = False
        self.on_message = on_message  # callback for received messages

    def connect(self, max_retries=5, retry_delay=1):
        def listen_wrapper():
            _buffer = ''
            while self._running:
                try:
                    chunk = self.sock.recv(4096)
                    if not chunk:
                        logger.warning("SocketClient: Connection closed by server.")
                        break
                    _buffer += chunk
                    delim = '\n'
                    while delim in _buffer:
                        line, _buffer = _buffer.split(delim, 1)
                        try:
                            msg = json.loads(line.decode('utf-8'))
                            logger.info("SocketClient: Received message: %s", msg)
                            if self.on_message:
                                reactor.callFromThread(self.on_message, convertUni2Str(msg))
                        except Exception:
                            logger.error("SocketClient: Error decoding message. Buffer: %r", line, exc_info=True)
                except Exception as e:
                    logger.error("SocketClient: Error in listen_wrapper: %s", str(e), exc_info=True)
                    logger.error("SocketClient: Buffer state at error: %r", _buffer)
                    break
            self._running = False

        def connect_attempt():
            attempt = 0
            while attempt < max_retries:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    # sock.settimeout(self.timeout)  # Removed for async/blocking recv
                    sock.connect((self.host, self.port))
                    self.sock = sock  # Only set after successful connect
                    self._running = True
                    logger.info("SocketClient: Connected to server.")
                    self._thread = threading.Thread(target=listen_wrapper)
                    self._thread.daemon = True
                    self._thread.start()
                    return
                except Exception:
                    logger.error("SocketClient: Connection failed (attempt %d/%d)", attempt+1, max_retries, exc_info=True)
                    self.sock = None
                    attempt += 1
                    if attempt < max_retries:
                        logger.info("SocketClient: Retrying in %d seconds...", retry_delay)
                        time.sleep(retry_delay)
            logger.error("SocketClient: Could not connect to server after retries.")

        if not self._running and not self.sock:
            t = threading.Thread(target=connect_attempt)
            t.daemon = True
            t.start()

    def send_json(self, data):
        retries = 0
        while (not self.sock or not self._running) and retries < 10:
            logger.info("SocketClient: Waiting for connection to send message...")
            time.sleep(0.2)
            retries += 1
        if not self.sock or not self._running:
            logger.error("SocketClient: Cannot send, not connected.")
            return
        message = json.dumps(data)
        logger.info("SocketClient: Sending message: %s", message)
        try:
            self.sock.sendall((message + '\n').encode('utf-8'))
        except Exception:
            logger.error("SocketClient: Error sending message:", exc_info=True)

    def close_connection(self):
        self._running = False
        if self.sock:
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
            except Exception:
                logger.warning("SocketClient: Exception during shutdown:", exc_info=True)
            try:
                self.sock.close()
            except Exception:
                logger.warning("SocketClient: Exception during close:", exc_info=True)
            self.sock = None
        if self._thread:
            self._thread = None
