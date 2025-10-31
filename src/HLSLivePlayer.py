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
from enigma import iPlayableService, eSize, eTimer
from Components.ActionMap import HelpableActionMap
from Components.config import config
from Components.Pixmap import Pixmap
from Components.ServiceEventTracker import InfoBarBase, ServiceEventTracker
from Components.Sources.COCCurrentService import COCCurrentService
from Screens.Screen import Screen
from Screens.HelpMenu import HelpableScreen
from Screens.InfoBarGenerics import InfoBarAudioSelection, InfoBarShowHide, InfoBarNotifications, InfoBarSubtitleSupport
from Tools.LoadPixmap import LoadPixmap
from .Debug import logger
from .__init__ import _
from .SkinUtils import getSkinName, getSkinPath
from .CockpitCueSheet import CockpitCueSheet
from .CockpitPVRState import CockpitPVRState
from .CockpitSeek import CockpitSeek
from .BoxUtils import getBoxType
from .ServiceUtils import getService
from .log_utils import write_log


class CockpitPlayerSummary(Screen):

    def __init__(self, session, parent):
        Screen.__init__(self, session, parent)
        self.skinName = getSkinName("CockpitPlayerSummary")


class HLSLivePlayer(
        Screen, HelpableScreen, InfoBarBase, InfoBarNotifications, InfoBarShowHide, InfoBarAudioSelection, InfoBarSubtitleSupport,
        CockpitCueSheet, CockpitSeek, CockpitPVRState
):

    ENABLE_RESUME_SUPPORT = False
    ALLOW_SUSPEND = True

    def __init__(self, session, _service, config_plugins_plugin, showMovieInfoEPGPtr=None, leave_on_eof=False, recording_start_time=0, timeshift=None, rec_files=None, service_center=None, stream=False):
        logger.info("rec_files: %s", rec_files)
        self.config_plugins_plugin = config_plugins_plugin
        self.showMovieInfoEPGPtr = showMovieInfoEPGPtr
        self.leave_on_eof = leave_on_eof
        self.stream = stream
        self.rec_files = [] if rec_files is None else rec_files
        self.section_index = -1
        self.service = self.getNextService()
        self.show_state_pic = False
        self.fast_winding_hint_message_showed = False
        self.wait_timer = eTimer()
        self.wait_timer_conn = self.wait_timer.timeout.connect(self.doEofInternal)
        self.alive_timer = eTimer()
        self.alive_timer_conn = self.alive_timer.timeout.connect(self.isPlaying)
        self.last_position = 0
        self.current_position = 0
        self.rec_dir = config.usage.default_path.value
        self.first_start = False
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
        CockpitCueSheet.__init__(self, self.service)

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
        CockpitSeek.__init__(
            self, session, self.service, event_start,
            recording_start_time, timeshift, service_center
        )
        CockpitPVRState.__init__(self)

        self.service_started = False
        self.onLayoutFinish.append(self.__onLayoutFinish)

    def createSummary(self):
        return CockpitPlayerSummary

    def __onLayoutFinish(self):
        logger.info("...")
        player_icon = "streamer.svg" if self.stream else "player.svg"
        self["player_icon"].instance.setPixmap(LoadPixmap(getSkinPath(
            "images/" + player_icon), cached=True, size=eSize(60, 60)))
        self.playSection(self.service)

    def getNextService(self):
        if self.rec_files:
            rec_file_dict = self.rec_files.pop(0)
            rec_file = rec_file_dict.get("rec_file", None)
            self.section_index = rec_file_dict.get("section_index", 0)
            logger.info("rec_file: %s, section_index: %d", rec_file, self.section_index)
            return getService(rec_file, "PlutoTV")
        return None

    def __serviceStarted(self):
        logger.info("=" * 70)
        logger.info("service_path: %s", self.service.getPath())
        # write_log(self.rec_dir, self.service.getPath(), self.section_index, "---", "service-started")
        self.hide()
        self.current_position = 0
        self.last_position = 0
        self.start_alive_timer()
        self.service_started = True

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
            service_ext = os.path.splitext(self.service.getPath())[1].lower()
            if service_ext == ".mp4" and not getBoxType().startswith("dream"):
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
        self.stop_alive_timer()
        self.session.nav.stopService()
        self.close()

    def isPlaying(self):
        self.current_position = self.getSeekPosition()
        logger.info("current_position: %d, last_position: %d", self.current_position, self.last_position)
        if self.current_position:
            if self.current_position == self.last_position:
                logger.info("Playback stopped without eos event")
                write_log(self.rec_dir, self.service.getPath(), self.section_index, "---", "no-eof-event")
                self.alive_timer.stop()
                self.doEofInternal()
            else:
                self.first_start = False
                self.last_position = self.current_position
        else:
            write_log(self.rec_dir, self.service.getPath(), self.section_index, "---", "position-0")
            self.alive_timer.stop()
            self.doEofInternal()

    def playSection(self, service):
        service_path = service.getPath()
        self.first_start = True
        logger.info("service_path: %s, file_size: %d", service_path, os.path.getsize(service_path))
        write_log(self.rec_dir, self.service.getPath(), self.section_index, "---", "play-section")
        self.showPVRStatePic(False)
        self.pvr_state_dialog.hide()
        self.session.nav.playService(service)

    def doEofInternal(self, playing=True):
        logger.info("playing: %s, self.execing: %s", playing, self.execing)

        self.alive_timer.stop()
        self.wait_timer.stop()

        self.showPVRStatePic(False)
        self.pvr_state_dialog.hide()
        self.hide()

        write_log(self.rec_dir, self.service.getPath(), self.section_index, "---", "end-of-file")

        if self.first_start:
            logger.info("restarting playback...")
            self.first_start = False
            self.playpause()
            self.start_alive_timer()
        else:
            logger.info("starting next service...")
            service = self.getNextService()
            if service:
                self.service = service
                self.playSection(service)
            else:
                logger.error("No recording files available, waiting...")
                write_log(self.rec_dir, self.service.getPath(), self.section_index, "---", "no-next-section")
                self.wait_timer.start(5000, True)

    def showMovies(self):
        logger.info("...")
