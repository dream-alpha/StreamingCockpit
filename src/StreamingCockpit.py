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
from .MediaList import MediaEntryComponent, MediaList
from .SocketClientHandler import SocketClientHandler
from .ConfigScreen import ConfigScreen
from .STC_Config import STC_Config
from .Debug import logger
from .Version import PLUGIN
from .__init__ import _


class StreamingCockpitSummary(Screen, object):
    pass


class StreamingCockpit(SocketClientHandler, Screen, object):
    def __init__(self, session, level, provider=None, category=None, socket_client=None, selection_config=None):
        self.socket_client = socket_client
        self.level = level
        self.category = category
        logger.info("Opening level: %d", self.level)
        self.stc_config = STC_Config()
        self.selection_config = self.stc_config.load() if selection_config is None else selection_config
        self.provider = provider
        self.provider_id = self.provider.get("provider_id", "none") if self.provider else "none"
        Screen.__init__(self, session)
        self.skinName = "StreamingCockpit"
        SocketClientHandler.__init__(self, session, socket_client)

        labels_red = [
            _("Exit"),
            _("Exit"),
            _("Exit"),
        ]
        self["key_red"] = Label()
        self["key_red"].setText(labels_red[level])

        labels_green = [
            "",
            "",
            "",
        ]
        self["key_green"] = Label()
        self["key_green"].setText(labels_green[level])

        labels_blue = [
            _("Settings"),
            _("Settings"),
            _("Settings"),
        ]
        self["key_blue"] = Label()
        self["key_blue"].setText(labels_blue[level])

        labels_yellow = [
            "",
            "",
            "",
        ]
        self["key_yellow"] = Label()
        self["key_yellow"].setText(labels_yellow[level])

        headers = [
            _("Providers"),
            _("Categories"),
            _("Medias"),
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
            "EXIT": self.back,
            "RED": self.exit
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
            logger.info("Selected media: %s", media)
            media_index = self["medialist"].getIndex()

            if self.level == 0:
                self.provider = media
            elif self.level == 1:
                self.category = media

            self.stc_config.set_index(
                self.selection_config,
                self.provider_id,
                self.level,
                media_index
            )

            if self.level < self.max_level:
                self.session.openWithCallback(
                    self.StreamingCockpitCallback,
                    StreamingCockpit,
                    self.level + 1,
                    self.provider,
                    self.category,
                    self.socket_client,
                    self.selection_config
                )
            else:
                logger.debug("Final selection reached: %s", media)
                self.startMovie(self.provider, media)

    def StreamingCockpitCallback(self, leave):
        logger.info("quit: %s", leave)
        if leave:
            self.close(True)

    def getMediaList(self):
        logger.info("Loading media list for level %d", self.level)
        try:
            self.requestMediaList(self.level, self.provider, self.category)
        except Exception as e:
            logger.error("Failed to load media list: %s", e)

    def updateMediaList(self, medialist):
        logger.info("Media list: %s", medialist)
        alist = []
        if medialist:
            alist = [MediaEntryComponent(media, self.level) for media in medialist]
        self["medialist"].setList(alist)
        media_index = self.stc_config.get_index(
            self.selection_config,
            self.provider_id,
            self.level
        )
        self["medialist"].setIndex(media_index)
        self["medialist"].show()
        self["header"].setText(self.headers[self.level])
        title = PLUGIN
        if self.level > 0 and self.provider:
            title += " - " + self.provider.get("name", "")
        self.setTitle(title)

    def showSettings(self):
        logger.info("...")
        self.session.openWithCallback(
            self.showSettingsCallback, ConfigScreen, config.plugins.streamingcockpit)

    def showSettingsCallback(self, changed=None):
        logger.info("Settings closed")
        if changed:
            logger.info("Settings changed")

    def back(self):
        self.stc_config.save(self.selection_config)
        self.close(False)

    def exit(self):
        self.stc_config.save(self.selection_config)
        self.close(True)

    def createSummary(self):
        return StreamingCockpitSummary
