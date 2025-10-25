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


from Components.config import config
from .Debug import logger
from .__init__ import _


class ConfigScreenInit():
    def __init__(self, _parent, session):
        self.session = session
        self.section = 400 * "¯"
        self.config_list = [
            # text, config, on save, on ok, e2 usage level, depends on rel parent, description
            (self.section, _("COCKPIT"), None, None, 0, [], ""),
            (_("Show advertisement"), config.plugins.streamingcockpit.show_ads, None, None, 0, [], _("Show advertisement instead of fillers")),
            (_("Resolution"), config.plugins.streamingcockpit.quality, None, None, 0, [], _("Select 'provider' or define maximum movie resolution")),
            (self.section, _("DEBUG"), None, None, 2, [], ""),
            (_("Log level"), config.plugins.streamingcockpit.debug_log_level, self.setLogLevel, None, 2, [], _("Select the debug log level."))
        ]

    @staticmethod
    def save(_conf):
        logger.debug("...")

    def openLocationBox(self, element):
        logger.debug("element: %s", element.value)
        return True

    def setLogLevel(self, element):
        logger.debug("element: %s", element.value)
        return True

    def validatePath(self, element):
        logger.debug("element: %s", element.value)
        return True
