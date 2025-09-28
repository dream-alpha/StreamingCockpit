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

from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.config import config
from Components.Label import Label
from Tools.BoundFunction import boundFunction
from .MediaList import MediaEntryComponent, MediaList
from .SocketClientHandler import SocketClientHandler
from .ConfigScreen import ConfigScreen
from .Debug import logger
from .__init__ import _


class StreamingCockpitSummary(Screen, object):
    pass


class StreamingCockpit(SocketClientHandler, Screen, object):
    def __init__(self, session, level, media=None, socket_client=None, provider=None):
        self.socket_client = socket_client
        self.level = level
        logger.info("Opening level: %d", self.level)
        self.media = media
        self.providers = None
        self.provider = provider
        self.categories = None
        self.channels = None
        self.channel = None
        Screen.__init__(self, session)
        self.skinName = "StreamingCockpit"
        SocketClientHandler.__init__(self, session, socket_client)

        labels_red = [
            _("Exit"),
            _("Exit"),
            _("Exit"),
        ]
        self["red"] = Label()
        self["red"].setText(labels_red[level])

        labels_green = [
            "",
            "",
            "",
        ]
        self["green"] = Label()
        self["green"].setText(labels_green[level])

        labels_blue = [
            _("Settings"),
            _("Settings"),
            _("Settings"),
        ]
        self["blue"] = Label()
        self["blue"].setText(labels_blue[level])

        labels_yellow = [
            "",
            "",
            "",
        ]
        self["yellow"] = Label()
        self["yellow"].setText(labels_yellow[level])

        headers = [
            _("Providers"),
            _("Categories"),
            _("Channels"),
        ]
        self.headers = headers
        self["header"] = Label()
        self["header"].setText(headers[level])

        self.max_level = len(headers) - 1

        self["medialist"] = MediaList([])

        actions = [
            {
                "GREEN": None,
                "YELLOW": None,
                "BLUE": self.showSettings,
            },
            {
                "GREEN": None,
                "YELLOW": None,
                "BLUE": self.showSettings,
            },
            {
                "GREEN": None,
                "YELLOW": None,
                "BLUE": self.showSettings,
            },
        ]
        action_map = {
            "OK": self.handleSelection,
            "EXIT": boundFunction(self.close, False),
            "RED": boundFunction(self.close, True)
        }
        merged_actions = action_map.copy()
        merged_actions.update(actions[level])

        self["actions"] = ActionMap(
            ["CockpitActions"],
            merged_actions
        )

        self.onLayoutFinish.append(self.layoutFinished)

    def layoutFinished(self):
        logger.info("Layout finished")
        self["header"].setText(_("Loading") + " " + self.headers[self.level] + "...")
        self["medialist"].hide()
        if self.level == 0:
            logger.info("Waiting for server to be ready...")
        else:
            self.getMediaList()

    def serverIsReady(self):
        logger.info("Server is ready")
        self.getMediaList()

    def handleSelection(self):
        current = self["medialist"].getCurrent()
        if current is not None:
            media = current[0]
            media_index = self["medialist"].getIndex()
            getattr(config.plugins.streamingcockpit, "selection%d_index" % self.level).value = media_index
            getattr(config.plugins.streamingcockpit, "selection%d_index" % self.level).save()

            if self.level == 0:
                self.provider = media

            if self.level < self.max_level:
                logger.info("Selected media: %s", media)
                self.session.openWithCallback(
                    self.StreamingCockpitCallback,
                    StreamingCockpit,
                    self.level + 1,
                    media,
                    self.socket_client,
                    self.provider
                )
            else:
                logger.debug("Final selection reached: %s", media)
                self.channel = media
                url = media.get("url", None)
                self.startMovie(url)

    def StreamingCockpitCallback(self, leave):
        logger.info("quit: %s", leave)
        if leave:
            self.close(True)

    def getMediaList(self):
        logger.info("Loading media list for level %d", self.level)
        medialist = []
        try:
            if self.level == 0:
                if self.providers is None:
                    self.requestMediaList()
                else:
                    self.updateMediaList(self.providers)
            elif self.level == 1:
                if self.categories is None:
                    self.requestMediaList(provider=self.provider)
                else:
                    self.updateMediaList(self.categories)
                logger.debug("Categories: %s", medialist)
            elif self.level == 2:
                if self.channels is None:
                    self.requestMediaList(provider=self.provider, category=self.media)
                else:
                    self.updateMediaList(self.channels)
                logger.debug("Channels: %s", medialist)
        except Exception as e:
            logger.error("Failed to load media list: %s", e)

    def updateMediaList(self, medialist):
        # logger.info("Media list: %s", medialist)
        alist = []
        if medialist:
            alist = [MediaEntryComponent(media) for media in medialist]
        self["medialist"].setList(alist)
        media_index = getattr(config.plugins.streamingcockpit, "selection%d_index" % self.level).value
        self["medialist"].setIndex(media_index)
        self["medialist"].show()
        self["header"].setText(self.headers[self.level])

    def showSettings(self):
        logger.info("...")
        self.session.openWithCallback(
            self.showSettingsCallback, ConfigScreen, config.plugins.streamingcockpit)

    def showSettingsCallback(self, _changed=None):
        pass

    def createSummary(self):
        return StreamingCockpitSummary
