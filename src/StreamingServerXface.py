# coding=utf-8
"""
StreamingServerXface.py
Interface for sending commands to a local streaming server via SocketClient and receiving responses.
Compatible with Python 2 and 3.
"""

import time
from .SocketClient import SocketClient


class StreamingServerXface(object):
    def __init__(self, port=5000, timeout=5):
        self.client = SocketClient(port=port, timeout=timeout)

    def start_stream(self, channel, path):
        cmd = {"command": "start", "channel": channel, "path": path}
        self.client.send_json(cmd)
        return self._wait_for_ready()

    def stop_stream(self):
        cmd = {"command": "stop"}
        self.client.send_json(cmd)
        return self._wait_for_ready()

    def _wait_for_ready(self, retries=10, delay=0.5):
        """Wait for a {"command": "ready"} response from the server."""
        for _ in range(retries):
            response = self.client.receive_json()
            if response and response.get("command") == "ready":
                return True
            time.sleep(delay)
        return False

    def close(self):
        self.client.close()

    def getPlaylist(self):
        cmd = {"command": "getPlaylist"}
        self.client.send_json(cmd)
        response = self.client.receive_json()
        if response and response.get("command") == "playlist":
            return response.get("playlist")
        return None

# Example usage:
# xface = StreamingServerXface(port=5000)
# if xface.start_stream("ZDF"):
#     print("Stream started and server is ready.")
# xface.stop_stream()
# xface.close()
