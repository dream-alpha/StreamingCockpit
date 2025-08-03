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


from Components.config import config, ConfigSelection, ConfigYesNo, ConfigDirectory, ConfigSubsection, ConfigNothing, NoSave
from .Debug import logger, log_levels, initLogging
from .__init__ import _


class ConfigInit():

    def __init__(self):
        logger.info("...")
        config.plugins.streamingcockpit = ConfigSubsection()
        config.plugins.streamingcockpit.fake_entry = NoSave(ConfigNothing())
        config.plugins.streamingcockpit.debug_log_level = ConfigSelection(
            default="INFO", choices=list(log_levels.keys()))
        config.plugins.streamingcockpit.askstopmovie = ConfigSelection(
            default="quit", choices=[("quit", _("Do nothing")), ("ask", _("Ask user"))])
        config.plugins.streamingcockpit.movie_dir = ConfigDirectory(
            default="/media/hdd/movie")
        config.plugins.streamingcockpit.movie_resume_at_last_pos = ConfigYesNo(
            default=False)
        config.plugins.streamingcockpit.movie_start_position = ConfigSelection(default="beginning", choices=[(
            "beginning", _("beginning")), ("first_mark", _("first mark")), ("event_start", _("event start"))])

        initLogging()
