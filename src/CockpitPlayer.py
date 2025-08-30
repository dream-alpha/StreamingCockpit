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
import time
from enigma import iPlayableService, eSize, eTimer
from Components.ActionMap import HelpableActionMap
from Components.Pixmap import Pixmap
from Components.ServiceEventTracker import InfoBarBase, ServiceEventTracker
from Components.Sources.COCCurrentService import COCCurrentService
from Screens.Screen import Screen
from Screens.HelpMenu import HelpableScreen
from Screens.InfoBarGenerics import InfoBarAudioSelection, InfoBarShowHide, InfoBarNotifications, InfoBarSubtitleSupport
from Tools.LoadPixmap import LoadPixmap
from .Debug import logger
from .__init__ import _
from .SkinUtils import getSkinName
from .CockpitCueSheet import CockpitCueSheet
from .CockpitPVRState import CockpitPVRState
from .CockpitSeek import CockpitSeek
from .BoxUtils import getBoxType
from .SkinUtils import getSkinPath
from .ServiceUtils import getService
from .log_utils import write_log


class CockpitPlayerSummary(Screen):

    def __init__(self, session, parent):
        Screen.__init__(self, session, parent)
        self.skinName = getSkinName("CockpitPlayerSummary")


class CockpitPlayer(
        Screen, HelpableScreen, InfoBarBase, InfoBarNotifications, InfoBarShowHide, InfoBarAudioSelection, InfoBarSubtitleSupport,
        CockpitCueSheet, CockpitSeek, CockpitPVRState
):

    ENABLE_RESUME_SUPPORT = False
    ALLOW_SUSPEND = True

    def __init__(self, session, service, config_plugins_plugin, showMovieInfoEPGPtr=None, leave_on_eof=False, recording_start_time=0, timeshift=None, service_center=None, stream=False):
        self.service = service
        self.service_ext = os.path.splitext(self.service.getPath())[1]
        self.config_plugins_plugin = config_plugins_plugin
        self.showMovieInfoEPGPtr = showMovieInfoEPGPtr
        self.leave_on_eof = leave_on_eof
        self.stream = stream
        self.show_state_pic = False
        self.fast_winding_hint_message_showed = False
        self.wait_timer = eTimer()
        self.wait_timer_conn = self.wait_timer.timeout.connect(self.doEofInternal)
        self.alive_timer = eTimer()
        self.alive_timer_conn = self.alive_timer.timeout.connect(self.isAlive)
        self.last_position = 0
        self.current_position = 0

        self.allowPiP = False
        self.allowPiPSwap = False

        Screen.__init__(self, session)
        HelpableScreen.__init__(self)
        self.skinName = getSkinName("CockpitPlayer")
        self["Service"] = COCCurrentService(session.nav, self)

        InfoBarShowHide.__init__(self)
        InfoBarBase.__init__(self)
        InfoBarAudioSelection.__init__(self)
        InfoBarNotifications.__init__(self)
        InfoBarSubtitleSupport.__init__(self)
        CockpitCueSheet.__init__(self, service)

        self["player_icon"] = Pixmap()

        self["actions"] = HelpableActionMap(
            self,
            "CockpitActions",
            {
                "OK": (self.ok, _("Infobar/Play")),
                "PLAY": (self.playpause, _("Play/Pause")),
                "STOP": (self.leavePlayer, _("Stop playback")),
                "EXIT": (self.leavePlayer, _("Stop playback")),
                "POWER": (self.leavePlayer, _("Stop playback")),
                "CHANNELUP": (self.skipForward, _("Skip forward")),
                "CHANNELDOWN": (self.skipBackward, _("Skip backward")),
                "INFOS": (self.showMovieInfoEPG, _("EPG Info")),
            },
            -2
        )

        self._event_tracker = ServiceEventTracker(
            screen=self,
            eventmap={
                iPlayableService.evStart: self.__serviceStarted
            }
        )

        event_start = False

        CockpitSeek.__init__(self, session, service, event_start,
                             recording_start_time, timeshift, service_center)
        CockpitPVRState.__init__(self)

        self.service_started = False
        self.onShown.append(self.__onShown)

    def createSummary(self):
        return CockpitPlayerSummary

    def __onShown(self):
        logger.info("service_started: %s", self.service_started)
        player_icon = "streamer.svg" if self.stream else "player.svg"
        self["player_icon"].instance.setPixmap(LoadPixmap(getSkinPath(
            "images/" + player_icon), cached=True, size=eSize(60, 60)))
        if not self.service_started:
            logger.info("First show, starting service: %s", self.service.getPath())
            self.session.nav.playService(self.service)

    def __serviceStarted(self):
        logger.info("=" * 70)
        logger.info("service_path: %s", self.service.getPath())
        write_log(self.service.getPath(), "none", "---", "---", msg="service-started")
        self.service_started = True
        self.hide()
        self.current_position = 0
        self.last_position = 0
        self.start_alive_timer()

    def start_alive_timer(self):
        self.alive_timer.start(1500)

    def stop_alive_timer(self):
        self.alive_timer.stop()

    def ok(self):
        if self.seekstate == self.SEEK_STATE_PLAY:
            self.stop_alive_timer()
            self.toggleShow()
        else:
            self.playpause()
            self.start_alive_timer()

    def playpause(self):
        if self.seekstate == self.SEEK_STATE_PAUSE:
            # workaround for video freeze problem after pause
            if self.service_ext == ".mp4" and not getBoxType().startswith("dream"):
                self.fast_winding_hint_message_showed = True
                self.playpauseService()
                self.showPVRStatePic(False)
                self.pvr_state_dialog.hide()
                self.seekBack()
                self.showPVRStatePic(True)
                self.pvr_state_dialog.show()
                self.playpauseService()
            else:
                self.playpauseService()
            self.start_alive_timer()
        else:
            self.playpauseService()
            self.stop_alive_timer()

    def showMovieInfoEPG(self):
        if self.showMovieInfoEPGPtr:
            self.showMovieInfoEPGPtr()

    def showPVRStatePic(self, show):
        self.show_state_pic = show

    def leavePlayer(self):
        logger.info("...")
        self.wait_timer.stop()
        self.alive_timer.stop()
        self.session.nav.stopService()
        self.close()

    def isAlive(self):
        self.current_position = self.getSeekPosition()
        logger.info("current_position: %d, last_position: %d", self.current_position, self.last_position)
        if self.current_position:
            if self.current_position == self.last_position:
                logger.info("Playback stopped without eos event")
                write_log(self.service.getPath(), "none", "---", "---", msg="no-eof-event")
                self.alive_timer.stop()
                self.doEofInternal()
            else:
                self.last_position = self.current_position
        else:
            write_log(self.service.getPath(), "none", "---", "---", msg="position-0")
            self.doEofInternal()

    def parseFilename(self, service):
        logger.info("...")
        parts = os.path.splitext(service.getPath())[0].split("_")
        base_path = parts[0]
        index = int(parts[1])
        return base_path, index

    def playSection(self, service_path):
        logger.info("service_path: %s, file_size: %d", service_path, os.path.getsize(service_path))
        write_log(service_path, "none", "---", "---", msg="play-section")
        self.service = getService(service_path, "PlutoTV")
        self.showPVRStatePic(False)
        self.pvr_state_dialog.hide()
        self.session.nav.playService(self.service)

    def nextSection(self, base_path, index):
        logger.info("...")
        index += 1
        path = "%s_%s.ts" % (base_path, index)
        return path

    def doEofInternal(self, playing=True):
        logger.info("playing: %s, self.execing: %s", playing, self.execing)

        self.alive_timer.stop()
        self.wait_timer.stop()

        self.showPVRStatePic(False)
        self.pvr_state_dialog.hide()

        base_path, index = self.parseFilename(self.service)
        write_log(self.service.getPath(), "none", index, "---", msg="end-of-file")

        if self.execing:
            next_section = self.nextSection(base_path, index)
            if os.path.exists(next_section):
                self.wait_timer.stop()
                self.current_position = 0
                self.last_position = 0
                logger.info("Time difference to now: %d", int(time.time()) - int(os.path.getctime(next_section)))
                write_log(next_section, "none", index + 1, "---", msg="now-playing")
                self.playSection(next_section)
            else:
                logger.warning("Next section does not exist, waiting for new section.")
                write_log(os.path.basename(self.service.getPath()), "none", index, "---", msg="no-next-section")
                self.wait_timer.start(5000, True)

    def showMovies(self):
        logger.info("...")
