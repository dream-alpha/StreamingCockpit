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
        self.buffering = config.plugins.streamingcockpit.buffering.value
        self.data_dir = os.path.join(config.plugins.streamingcockpit.data_dir.value, ID)
        self.providers_dir = config.plugins.streamingcockpit.providers_dir.value
        self.first = True
        self.rec_files = []
        self.socket_client.connect()

    def requestMediaList(self, provider=None, category=None):
        """Request medialist from server and wait for response."""
        logger.info("Requesting medialist: provider=%s, category=%s", provider, category)

        # Prepare request based on parameters
        if provider is None:
            request = ["get_providers", {"data_dir": self.providers_dir}]
        elif category is None:
            request = ["get_categories", {"provider": provider, "data_dir": self.data_dir}]
        else:
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
            channel = args.get("channel", "unknown")
            if reason == "error":
                self.loading.stop()
                logger.error("Error occurred while playing back channel: %s", channel)
                self.session.openWithCallback(self.MessageBoxCallback, MessageBox, _("Error occurred while playing back stream"), MessageBox.TYPE_ERROR)
            else:
                self.loading.stop()
                logger.info("Stopping playback for channel: %s", channel)
        elif command == "get_providers":
            providers = args.get("data", [])
            logger.info("Received providers: %s", providers)
            self.updateMediaList(providers)
        elif command == "get_categories":
            categories = args.get("data", [])
            logger.info("Received categories: %s", categories)
            self.updateMediaList(categories)
        elif command == "get_media_items":
            media_items = args.get("data", [])
            logger.info("Received media items: %s", media_items)
            self.updateMediaList(media_items)
        else:
            logger.warning("Unknown command received: %s", command)

    def startMovie(self, channel_uri, provider):
        logger.info("channel_uri: %s", channel_uri)
        rec_dir = os.path.normpath(config.usage.default_path.value)
        args = {"url": channel_uri, "rec_dir": rec_dir, "show_ads": config.plugins.streamingcockpit.show_ads.value, "buffering": self.buffering, "provider": provider}
        self.socket_client.send_message(["start", args])
        self.loading.start(-1, _("Starting playback..."))

    def playMovie(self):
        logger.info("...")
        event_list = [
            [
                "%s - %s" % (self.provider.get('name'), self.channel.get('name')),
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
