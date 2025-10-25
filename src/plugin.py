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


from Plugins.Plugin import PluginDescriptor
from .ConfigInit import ConfigInit
from .StreamingCockpit import StreamingCockpit
from .SkinUtils import loadPluginSkin
from .Version import VERSION
from .DelayTimer import DelayTimer
from .chroot_utils import start_ubuntu_plugin, stop_ubuntu_plugin, umount_chroot, bind_media_to_chroot, unbind_media_from_chroot
from .SocketClient import SocketClient
from .Debug import logger
from .Version import PLUGIN
from .__init__ import _

UBUNTU_ROOT = "/data/ubuntu"
server_proc = None
socket_client = None
last_service = None
global_session = None


def startServer():
    global server_proc
    try:
        # mount media directories
        bind_media_to_chroot(UBUNTU_ROOT)
        # Start the server in a chroot environment
        server_proc = start_ubuntu_plugin(UBUNTU_ROOT, "/root/plugins/streamingserver/main.py")
        logger.info("Started server in chroot /data/ubuntu using venv")
    except Exception as e:
        logger.error("Failed to start server in chroot with venv: %s", e)


def stopServer():
    if server_proc:
        stop_ubuntu_plugin(UBUNTU_ROOT, server_proc)
        unbind_media_from_chroot(UBUNTU_ROOT)
        DelayTimer(100, umount_chroot, UBUNTU_ROOT)


def main(session, **__kwargs):
    global socket_client, last_service, global_session
    global_session = session
    last_service = session.nav.getCurrentlyPlayingServiceReference()
    session.nav.stopService()
    startServer()
    socket_client = SocketClient(port=5000)
    session.openWithCallback(StreamingCockpitCallback, StreamingCockpit, 0, socket_client=socket_client)


def StreamingCockpitCallback(_dummy=None):
    if socket_client:
        socket_client.close_connection()
    stopServer()
    global_session.nav.playService(last_service)


def autoStart(reason, **kwargs):
    if reason == 0:  # startup
        if "session" in kwargs:
            logger.info("+++ Version: %s starts...", VERSION)
            loadPluginSkin("skin.xml")
    elif reason == 1:  # shutdown
        logger.info("--- shutdown")


def Plugins(**__kwargs):
    ConfigInit()
    descriptors = [
        PluginDescriptor(
            where=[
                PluginDescriptor.WHERE_AUTOSTART,
                PluginDescriptor.WHERE_SESSIONSTART,
            ],
            fnc=autoStart
        ),
        PluginDescriptor(
            name=PLUGIN,
            description=_("Watch online videos"),
            icon="StreamingCockpit.svg",
            where=[
                PluginDescriptor.WHERE_PLUGINMENU,
                PluginDescriptor.WHERE_EXTENSIONSMENU,
            ],
            fnc=main
        )
    ]

    return descriptors
