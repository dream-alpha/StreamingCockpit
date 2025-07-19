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


import subprocess
from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.config import config
from Components.Sources.StaticText import StaticText
from Tools.BoundFunction import boundFunction
from .Debug import logger
from .__init__ import _
from .ChannelSelection import ChannelSelection
from .ServiceUtils import getService
from .CockpitPlayer import CockpitPlayer


class StreamingCockpit(Screen, ChannelSelection):
    def __init__(self, session):
        Screen.__init__(self, session)
        self.skinName = "StreamingCockpit"
        ChannelSelection.__init__(self, session)
        self.last_service = self.session.nav.getCurrentlyPlayingServiceReference()

        self["key_red"] = StaticText(_("Exit"))
        self["key_green"] = StaticText(_("Playlist"))
        self["key_yellow"] = StaticText()
        self["key_blue"] = StaticText()

        self["actions"] = ActionMap(
            ["STC_Actions"],
            {
                "cancel": self.pressClose,
                "red": self.pressClose,
		"green": self.openChannelSelection
            }
        )
        try:
            # subprocess.Popen([
            #     "chroot", "/data/ubuntu", "/venv/bin/python", "/streamingserver.py"
            # ])
            logger.info("Started streamingserver.py in chroot /data/ubuntu using venv")
        except Exception as e:
            logger.error("Failed to start streamingserver.py in chroot with venv: %s", e)

        self.onLayoutFinish.append(self.__onLayoutFinish)

    def __onLayoutFinish(self):
        logger.info("...")

    def playMovie(self, url, path):
        logger.info("url: %s, path: %s", url, path)
        uri = path
        if uri:
            logger.debug("Playing movie from URI: %s", uri)
            service = getService(uri, "pluto")
            self.session.openWithCallback(boundFunction(self.playMovieCallback, path), CockpitPlayer, service,
                                          config.plugins.streamingcockpit, self.pressInfo, service_center=self.service_center)

    def playMovieCallback(self, path):
        logger.info("path: %s", path)

    def pressGreen(self):
        self.openChannelSelection()

    def pressClose(self):
        logger.info("...")
        self.session.nav.playService(self.last_service)
        self.close()
