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
import struct
import json
import threading
import time
from twisted.internet import reactor
from .UnicodeUtils import convertUni2Str
from .Debug import logger


def send_length_prefixed_message(sock, message):
    """Send a JSON message with length prefix (standard approach for large TCP data)"""
    json_data = json.dumps(message, ensure_ascii=False).encode('utf-8')
    length_prefix = struct.pack('>I', len(json_data))  # 4-byte big-endian length
    sock.sendall(length_prefix + json_data)


def recv_length_prefixed_message(sock):
    """Receive a length-prefixed JSON message"""
    # First, receive the 4-byte length prefix
    length_data = ''
    while len(length_data) < 4:
        chunk = sock.recv(4 - len(length_data))
        if not chunk:
            raise RuntimeError("Connection closed while reading length prefix")
        length_data += chunk

    # Unpack the length
    message_length = struct.unpack('>I', length_data)[0]

    # Now receive the exact message
    json_data = ''
    while len(json_data) < message_length:
        chunk = sock.recv(message_length - len(json_data))
        if not chunk:
            raise RuntimeError("Connection closed while reading message")
        json_data += chunk

    # Parse and return the JSON
    return json.loads(json_data.decode('utf-8'))


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
            while self._running:
                try:
                    # Receive length-prefixed message
                    msg = recv_length_prefixed_message(self.sock)
                    logger.info("SocketClient: Received message: %s", msg)
                    if self.on_message:
                        reactor.callFromThread(self.on_message, convertUni2Str(msg))
                except Exception as e:
                    logger.error("SocketClient: Error in listen_wrapper: %s", str(e), exc_info=True)
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

    def send_message(self, data):
        retries = 0
        while (not self.sock or not self._running) and retries < 10:
            logger.info("SocketClient: Waiting for connection to send message...")
            time.sleep(0.2)
            retries += 1
        if not self.sock or not self._running:
            logger.error("SocketClient: Cannot send, not connected.")
            return
        logger.info("SocketClient: Sending message: %s", data)
        try:
            send_length_prefixed_message(self.sock, data)
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
