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


from Screens.ChoiceBox import ChoiceBox
from Components.config import config
from .Debug import logger
from .__init__ import _


class ChannelSelection:
    def __init__(self, session):
        self.session = session
        self.selection_level = 0
        self.selection_0_index = 0
        self.selection_0_key = ""
        self.selection_1_index = 0
        self.choices = []
        self.channels_dict = {}

    def create_choices(self):
        self.choices = []
        if self.selection_level == 0:
            for key in sorted(self.channels_dict.keys()):
                self.choices.append((key, key))
        else:
            channels = self.channels_dict[self.selection_0_key]
            for channel in channels:
                logger.debug("channel: %s", channel)
                name = channel.get("name", "n/a")
                self.choices.append((name, channel))
                self.choices.sort(key=lambda x: x[0])
        logger.debug("choices: %s", self.choices)
        return self.choices

    def openChannelSelection(self, first=False):
        logger.info("channels_dict: %s", self.channels_dict)
        if first:
            self.selection_level = int(config.plugins.streamingcockpit.selection_level.value)
            self.selection_0_index = int(config.plugins.streamingcockpit.selection_0_index.value)
            self.selection_0_key = config.plugins.streamingcockpit.selection_0_key.value
            self.selection_1_index = int(config.plugins.streamingcockpit.selection_1_index.value)

        title = _("PlutoTV - Categories") if self.selection_level == 0 else _("PlutoTV - Channels")
        selection = self.selection_0_index if self.selection_level == 0 else self.selection_1_index
        self.create_choices()
        self.session.openWithCallback(
            self.openChannelSelectionCallback,
            ChoiceBox,
            title=_("Channel selection"),
            list=self.choices,
            selection=selection,
            titlebartext=title,
            keys=[]
        )

    def zapChannel(self, _channel_uri):
        logger.error("Overridden in subclass")

    def openChannelSelectionCallback(self, selection):
        logger.info("selection: %s", selection)
        if selection:
            if self.selection_level == 0:
                self.selection_0_index = self.choices.index(selection)
                self.selection_0_key = selection[1]
                self.selection_level = 1
                self.openChannelSelection()
            else:
                self.selection_1_index = self.choices.index(selection)
                channel_uri = selection[1]["url"]
                self.zapChannel(channel_uri)

                config.plugins.streamingcockpit.selection_level.value = self.selection_level
                config.plugins.streamingcockpit.selection_0_index.value = self.selection_0_index
                config.plugins.streamingcockpit.selection_1_index.value = self.selection_1_index
                config.plugins.streamingcockpit.selection_0_key.value = self.selection_0_key
                config.plugins.streamingcockpit.save()
        elif self.selection_level == 1:
            self.selection_level = 0
            self.openChannelSelection()
