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
from Components.config import config
from Screens.MessageBox import MessageBox
from .CockpitPlayer import CockpitPlayer
from .Loading import Loading
from .Debug import logger
from .ServiceCenter import ServiceCenter
from .Version import ID
from .__init__ import _


class SocketClientHandler():
    def __init__(self, session, socket_client):
        self.session = session
        self.socket_client = socket_client
        self.socket_client.on_message = self.handle_message
        self.loading = Loading(self, None)
        self.service_center = None
        self.data_dir = os.path.join(config.plugins.streamingcockpit.data_dir.value, ID)
        self.providers_dir = config.plugins.streamingcockpit.providers_dir.value
        self.first = True
        self.rec_files = []
        self.socket_client.connect()

    def requestMediaList(self, level, provider, category):
        """Request medialist from server and wait for response."""
        logger.info("Requesting medialist: level: %s, provider: %s, category: %s", level, provider, category)

        # Prepare request based on level
        if level == 0:
            request = ["get_providers", {"data_dir": self.providers_dir}]
        elif level == 1:
            request = ["get_categories", {"provider": provider, "data_dir": self.data_dir}]
        elif level == 2:
            request = ["get_media_items", {"provider": provider, "category": category, "data_dir": self.data_dir}]

        self.socket_client.send_message(request)

    def handle_message(self, message):
        """Handle incoming messages from the server."""
        logger.info("Received message: %s", message)
        command = message[0]
        args = message[1] if len(message) > 1 else {}
        if command == "ready":
            logger.info("Server is ready.")
            self.serverIsReady()
        elif command == "start":
            self.rec_files.append(args)
            if self.first:
                self.first = False
                self.loading.stop()
                self.playMovie()
        elif command == "stop":
            reason = args.get("reason", "none")
            if reason == "error":
                self.loading.stop()
                logger.error("Error occurred during playback.")
                self.session.openWithCallback(self.MessageBoxCallback, MessageBox, _("Error occurred while playing back stream"), MessageBox.TYPE_ERROR)
            else:
                self.loading.stop()
                logger.info("Stopping playback for media: %s", self.media.get("title", "unknown"))
        elif command in ("get_providers", "get_categories", "get_media_items"):
            data = args.get("data", [])
            logger.info("%s: %s", command, data)
            self.updateMediaList(data)
        else:
            logger.warning("Unknown command received: %s", command)

    def startMovie(self, provider, media):
        self.media = media
        logger.info("media_url: %s", self.media.get("url", ""))
        args = {
            "url": self.media.get("url", ""),
            "rec_dir": os.path.normpath(config.usage.default_path.value),
            "show_ads": config.plugins.streamingcockpit.show_ads.value,
            "buffering": config.plugins.streamingcockpit.buffering.value,
            "provider": provider,
            "av1": config.plugins.streamingcockpit.av1.value,
            "quality": config.plugins.streamingcockpit.quality.value
        }
        self.socket_client.send_message(["start", args])
        self.loading.start(-1, _("Starting playback..."))

    def playMovie(self):
        logger.info("...")
        media_title = self.media.get("title", "")
        if not media_title:
            media_title = self.media.get("name", "")
        event_list = [
            [
                "%s - %s" % (self.provider.get('title'), media_title),
                "",
                "",
                0,
                0,
                0
            ]
        ]
        self.service_center = ServiceCenter(event_list)
        logger.info("event_list: %s", event_list)
        self.session.openWithCallback(
            self.playMovieCallback,
            CockpitPlayer,
            None,
            config.plugins.streamingcockpit,
            self.showInfo,
            rec_files=self.rec_files,
            service_center=self.service_center,
            stream=False
        )

    def playMovieCallback(self):
        logger.info("...")
        self.socket_client.send_message(["stop", {}])
        self.loading.stop()
        self.first = True
        self.rec_files = []

    def MessageBoxCallback(self, answer):
        """Callback for MessageBox."""
        logger.info("MessageBox answer: %s", answer)

    def showInfo(self):
        return
