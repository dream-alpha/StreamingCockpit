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
from enigma import iPlayableService, eSize
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
from .DelayTimer import DelayTimer


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
                iPlayableService.evStart: self.__serviceStarted,
                iPlayableService.evEnd: self.__serviceEnded,
                iPlayableService.evSOF: self.__serviceSOF,
                iPlayableService.evEOF: self.__serviceEOF,
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
        logger.info("...")
        player_icon = "streamer.svg" if self.stream else "player.svg"
        self["player_icon"].instance.setPixmap(LoadPixmap(getSkinPath(
            "images/" + player_icon), cached=True, size=eSize(60, 60)))
        if not self.service_started:
            self.session.nav.playService(self.service)

    def __serviceStarted(self):
        logger.info("self.is_closing: %s", self.is_closing)
        self.service_started = True
        self.hide()

    def __serviceEnded(self):
        logger.info("...")
        self.service_started = False
        self.hide()

    def __serviceSOF(self):
        logger.info("...")

    def __serviceEOF(self):
        logger.info("...")

    def ok(self):
        if self.seekstate == self.SEEK_STATE_PLAY:
            self.toggleShow()
        else:
            self.playpause()

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
        else:
            self.playpauseService()

    def showMovieInfoEPG(self):
        if self.showMovieInfoEPGPtr:
            self.showMovieInfoEPGPtr()

    def showPVRStatePic(self, show):
        self.show_state_pic = show

    def leavePlayer(self):
        logger.info("...")
        self.session.nav.stopService()
        self.close()

    def parseFilename(self, service):
        logger.info("...")
        parts = os.path.splitext(service.getPath())[0].split("_")
        base_path = parts[0]
        resolution = parts[1]
        index = int(parts[2])
        return base_path, resolution, index

    def playSection(self, service_path):
        logger.info("service_path: %s, file_size: %d", service_path, os.path.getsize(service_path))
        self.service = getService(service_path, "PlutoTV")
        self.showPVRStatePic(False)
        self.pvr_state_dialog.hide()
        self.session.nav.playService(self.service)

    def nextSection(self, base_path, index):
        logger.info("...")
        index += 1
        for resolution in ["l", "h"]:
            path = "%s_%s_%s.ts" % (base_path, resolution, index)
            if os.path.exists(path):
                break
        else:
            path = None
        return path

    def checkPlaying(self, service):
        logger.info("...")
        if not self.service_started:
            logger.error("Restarting current service failed: %s", service.getPath())
            self.doEofInternal(service)
        else:
            logger.info("service is playing: %s", service.getPath())

    def startCurrentService(self, service):
        logger.info("current service: %s", service.getPath())
        self.session.nav.playService(service)
        DelayTimer(500, self.checkPlaying, service)

    def doEofInternal(self, playing=True):
        logger.info("playing: %s, self.execing: %s", playing, self.execing)
        self.showPVRStatePic(False)
        self.pvr_state_dialog.hide()

        base_path, _resolution, index = self.parseFilename(self.service)
        if self.execing:
            # self.session.nav.stopService()
            next_section = self.nextSection(base_path, index)
            if next_section:
                # logger.info("Playing next section: %s, created at: %d", next_section, int(os.path.getctime(next_section)))
                logger.info("Time difference to now: %d", int(time.time()) - int(os.path.getctime(next_section)))
                self.playSection(next_section)
            else:
                logger.warning("Next section does not exist, restarting current section.")
                self.playpause()
                self.service_started = False
                self.startCurrentService(self.service)

    def showMovies(self):
        logger.info("...")
