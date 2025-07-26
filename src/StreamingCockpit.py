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
import json
import subprocess
from Screens.Screen import Screen
from Screens.ChoiceBox import ChoiceBox
from Components.ActionMap import ActionMap
from Components.config import config
from Components.Sources.StaticText import StaticText
from Tools.BoundFunction import boundFunction
from .Debug import logger
from .__init__ import _
from .ServiceUtils import getService
from .CockpitPlayer import CockpitPlayer
from .ServiceCenter import ServiceCenter
from .SocketClient import SocketClient
from .CallLater import callLater
from .chroot_utils import mount_specials, umount_specials_lazy, mount_bind


class StreamingCockpit(Screen, SocketClient):

    def __init__(self, session):
        Screen.__init__(self, session)
        self.skinName = "StreamingCockpit"
        SocketClient.__init__(self, port=5000, on_message=self.handle_message)
        self.selection = 0
        self.choices = []
        self.playlist = []
        self.last_service = self.session.nav.getCurrentlyPlayingServiceReference()
        self.service_center = ServiceCenter([])
        self.root = "/data/ubuntu"
        self.movie_src = "/media/hdd/movie"
        self.movie_dst = "/data/ubuntu/media/hdd/movie"

        self["key_red"] = StaticText(_("Exit"))
        self["key_green"] = StaticText(_("Playlist"))
        self["key_yellow"] = StaticText()
        self["key_blue"] = StaticText()

        self["actions"] = ActionMap(
            ["CockpitActions"],
            {
                "EXIT": self.exit,
                "RED": self.exit,
                "GREEN": self.openChannelSelection
            }
        )

        try:
            # Make sure movie directory exists
            if not os.path.exists(self.movie_dst):
                os.makedirs(self.movie_dst)

            mount_specials(self.root)
            # mount movie directory
            mount_bind(self.movie_src, self.movie_dst)

            # Start the streaming server in a chroot environment
            self.server_proc = subprocess.Popen([
                "chroot", "/data/ubuntu", "/root/venv/bin/python", "/root/plugins/streamingserver/main.py", "--server"
            ])
            logger.info("Started streamingserver.py in chroot /data/ubuntu using venv with --server")
        except Exception as e:
            logger.error("Failed to start streamingserver.py in chroot with venv: %s", e)

        self.connect()  # Initialize the socket client connection
        self.onLayoutFinish.append(self.__onLayoutFinish)

    def __onLayoutFinish(self):
        logger.info("...")
        self.sendCommand({"command": "get_playlist", "args": []})

    def sendCommand(self, message):
        """Send command."""
        self.send_json(message)

    def handle_message(self, message):
        """Handle incoming messages from the server."""
        logger.info("Received message: %s", message)
        command = message.get("command", "None")
        if command == "get_playlist":
            self.playlist = message.get("args", [])[0]
            self.openChannelSelection()
        elif command == "start":
            rec_file = message.get("args", [None, None])[1]
            self.playMovie(rec_file)
        elif command == "stop":
            pass  # Handle stop command if needed
        else:
            logger.warning("Unknown command received: %s", command)

    def openChannelSelection(self):
        self.choices = []
        for channel in self.playlist:
            logger.debug("channel: %s", channel)
            self.choices.append((channel["display_name"], channel["channel_id"]))
        self.session.openWithCallback(
            self.openChannelSelectionCallback,
            ChoiceBox,
            title=_("Channel selection"),
            list=self.choices,
            selection=self.selection,
            titlebartext="StreamingCockpit" + " - " + ("PlutoTV"),
            keys=[]
        )

    def openChannelSelectionCallback(self, selection):
        logger.info("selection: %s", selection)
        if selection:
            self.selection = self.choices.index(selection)
            channel_uri = selection[1]
            rec_file = "/media/hdd/movie/pluto.ts"
            self.sendCommand({"command": "start", "args": [channel_uri, rec_file]})

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
        self.openChannelSelection()

    def exit(self):
        logger.info("...")
        self.close_connection()
        if hasattr(self, 'server_proc') and self.server_proc:
            self.server_proc.terminate()
            self.server_proc.wait()
            subprocess.call(["umount", self.movie_dst])
        umount_specials_lazy(self.root)
        try:
            subprocess.call(["umount", "-l", self.movie_dst])
        except Exception:
            pass

        self.session.nav.playService(self.last_service)
        self.close_connection()
        self.close()
