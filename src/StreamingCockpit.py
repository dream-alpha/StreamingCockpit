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


import os
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.ActionMap import ActionMap
from Components.config import config
from Components.Sources.StaticText import StaticText
from Tools.BoundFunction import boundFunction
from .ConfigScreen import ConfigScreen
from .Debug import logger
from .ServiceUtils import getService
from .CockpitPlayer import CockpitPlayer
from .ServiceCenter import ServiceCenter
from .SocketClient import SocketClient
from .ChannelSelection import ChannelSelection
from .chroot_utils import start_ubuntu_plugin, stop_ubuntu_plugin, bind_media_to_chroot, unbind_media_from_chroot
from .Loading import Loading
from .DelayTimer import DelayTimer
from .__init__ import _


BUFFERING = 4

class StreamingCockpit(Screen, ChannelSelection, SocketClient):

    def __init__(self, session):
        Screen.__init__(self, session)
        ChannelSelection.__init__(self, session)
        self.skinName = "StreamingCockpit"
        SocketClient.__init__(self, port=5000, on_message=self.handle_message)
        self.channels_dict = {}
        self.last_service = self.session.nav.getCurrentlyPlayingServiceReference()
        self.session.nav.stopService()
        self.service_center = ServiceCenter([])
        self.loading = Loading(self, None)
        self.root = "/data/ubuntu"
        self.media_src = "/media"
        self.media_dst = self.root + self.media_src

        self["key_red"] = StaticText(_("Exit"))
        self["key_green"] = StaticText(_("Playlist"))
        self["key_yellow"] = StaticText()
        self["key_blue"] = StaticText(_("Settings"))

        self["actions"] = ActionMap(
            ["CockpitActions"],
            {
                "MENU": self.showSettings,
                "EXIT": self.exit,
                "RED": self.exit,
                "GREEN": boundFunction(self.openChannelSelection, True),
                "BLUE": self.showSettings
            }
        )

        try:
            # mount media directories
            bind_media_to_chroot(self.root)
            # Start the streaming server in a chroot environment
            self.server_proc = start_ubuntu_plugin(self.root, "/root/plugins/streamingserver/main.py")
            logger.info("Started streamingserver.py in chroot /data/ubuntu using venv")
        except Exception as e:
            logger.error("Failed to start streamingserver.py in chroot with venv: %s", e)

        self.onLayoutFinish.append(self.__onLayoutFinish)

    def __onLayoutFinish(self):
        logger.info("...")
        self.connect()  # Initialize the socket client connection


    def sendCommand(self, message):
        """Send command."""
        self.send_json(message)

    def handle_message(self, message):
        """Handle incoming messages from the server."""
        logger.info("Received message: %s", message)
        command = message.get("command", "None")
        if command == "ready":
            self.sendCommand({"command": "get_playlist", "args": []})
        elif command == "get_playlist":
            self.channels_dict = message.get("args", [{}])[0]
            self.openChannelSelection(True)
        elif command == "start":
            args = message.get("args", ["", "", ""])
            rec_file = args[1]
            segment_index = args[2]
            if segment_index <= BUFFERING:
                self.loading.setSeconds(BUFFERING - segment_index)
            elif segment_index == BUFFERING + 1:
                self.loading.stop()
                DelayTimer(50, self.playMovie, rec_file)
        elif command == "stop":
            args = message.get("args", ["", "", ""])
            reason = args[0]
            channel = args[1]
            rec_file = args[2]
            if reason == "error":
                self.loading.stop()
                logger.error("Error occurred while playing back channel: %s", channel)
                self.session.openWithCallback(self.MessageBoxCallback, MessageBox, _("Error occurred while playing back stream"), MessageBox.TYPE_ERROR)
            else:
                self.loading.stop()
                logger.info("Stopping playback for channel: %s", channel)
        else:
            logger.warning("Unknown command received: %s", command)

    def MessageBoxCallback(self, answer):
        """Callback for MessageBox."""
        logger.info("MessageBox answer: %s", answer)
        self.openChannelSelection()

    def zapChannel(self, channel_uri):
        logger.info("channel_uri: %s", channel_uri)
        rec_file = os.path.join(config.usage.default_path.value, "pluto.ts")
        self.sendCommand({"command": "start", "args": [channel_uri, rec_file, config.plugins.streamingcockpit.show_ads.value]})
        self.loading.start(-1, _("Starting playback..."))

    def playMovie(self, rec_file):
        logger.info("rec_file: %s", rec_file)
        service = getService(rec_file)
        self.session.openWithCallback(boundFunction(self.playMovieCallback, rec_file),
                                      CockpitPlayer,
                                      service,
                                      config.plugins.streamingcockpit,
                                      self.showInfo,
                                      service_center=self.service_center,
                                      stream=False)

    def showInfo(self):
        return

    def playMovieCallback(self, path):
        logger.info("path: %s", path)
        self.sendCommand({"command": "stop", "args": []})
        self.loading.stop()
        self.openChannelSelection()

    def showSettings(self):
        logger.info("...")
        self.session.openWithCallback(
            self.showSettingsCallback, ConfigScreen, config.plugins.streamingcockpit)

    def showSettingsCallback(self, _changed=None):
        pass

    def exit(self):
        logger.info("...")
        self.close_connection()
        if hasattr(self, 'server_proc') and self.server_proc:
            stop_ubuntu_plugin(self.root, self.server_proc)
            unbind_media_from_chroot(self.root)

        self.session.nav.playService(self.last_service)
        self.close_connection()
        self.close()
