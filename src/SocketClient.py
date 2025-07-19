# coding=utf-8
"""
SocketClient.py
A simple socket client for sending and receiving JSON data to/from a server on localhost.
Compatible with Python 2 and 3.
"""

import socket
import json

class SocketClient(object):
    def __init__(self, host='127.0.0.1', port=5000, timeout=5):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.sock = None

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        self.sock.connect((self.host, self.port))

    def send_json(self, data):
        if not self.sock:
            self.connect()
        message = json.dumps(data)
        # Add newline as delimiter for message framing
        self.sock.sendall(message.encode('utf-8') + b'\n')

    def receive_json(self):
        if not self.sock:
            self.connect()
        _buffer = b''
        while True:
            chunk = self.sock.recv(4096)
            if not chunk:
                break
            _buffer += chunk
            if b'\n' in _buffer:
                line, _buffer = _buffer.split(b'\n', 1)
                return json.loads(line.decode('utf-8'))
        return None

    def close(self):
        if self.sock:
            self.sock.close()
            self.sock = None

# Example usage:
# client = SocketClient(port=5000)
# client.send_json({'msg': 'hello'})
# response = client.receive_json()
# print(response)
# client.close()
