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


import json
from Screens.ChoiceBox import ChoiceBox
from .Debug import logger
from .__init__ import _
from .StreamingServerXface import StreamingServerXface
from .CallLater import callLater


class ChannelSelection():
    def __init__(self, session):
        self.session = session

    def zapToChannel(self, channel_uri, path):
        logger.info("Zapping to channel: %s", channel_uri)
        xface = StreamingServerXface()
        success = xface.start_stream(channel_uri, path)
        xface.close()
        if success:
            logger.info("Channel started successfully.")
        else:
            logger.error("Failed to start channel.")

    def getPlaylist(self):
        logger.info("Fetching playlist...")
        playlist = []
        # xface = StreamingServerXface()
        # playlist = xface.getPlaylist()
        # xface.close()
        with open("/usr/lib/enigma2/python/Plugins/Extensions/StreamingCockpit/de.json", "r") as f:
            data = json.load(f)
            for entry in data:
                logger.debug("playlist entry: %s", entry)
                playlist.append((entry["display_name"], entry["channel_id"]))
        logger.info("Received playlist: %s", playlist)
        return playlist

    def openChannelSelection(self):
        logger.info("...")
        choices = []
        playlist = self.getPlaylist()
        if playlist:
            for channel in playlist:
                logger.debug("channel: %s", channel)
                choices.append((str(channel[0]), str(channel[1])))
        self.session.openWithCallback(
            self.openChannelSelectionCallback,
            ChoiceBox,
            title=_("Channel selection"),
            list=choices,
            titlebartext="StreamingCockpit" + " - " + ("PlutoTV"),
            keys=[]
        )

    def openChannelSelectionCallback(self, selection):
        logger.info("selection: %s", selection)
        if selection:
            channel_uri = selection[1]
            path = selection[0] + ".ts"
            # self.zapToChannel(channel_uri, path)
            # callLater(0.1, self.playMovie, channel_uri, path)
