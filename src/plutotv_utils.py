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
# <http://www.gnu.org/licenses>.


import json
import datetime
import os
from .Debug import logger

ID = "UVP"


DATA_DIR = "/etc/enigma2" + "/" + ID
CHANNELS_FILE = os.path.join(DATA_DIR, "%s/channels.json")
CATEGORIES_FILE = os.path.join(DATA_DIR, "%s/categories.json")


def get_providers():
    """
    Returns a list of providers.
    """
    logger.info("Fetching providers")
    with open('/etc/enigma2/UVP/providers.json', 'r') as f:
        providers = json.load(f)
    return providers


def get_categories(provider):
    """
    Returns a list of categories.
    """
    logger.info("Fetching categories for provider: %s", provider)
    with open(CATEGORIES_FILE % provider["path"], 'r') as f:
        categories = json.load(f)
    return categories


def get_channels(provider, category):
    """
    Returns a list of channels.
    """
    logger.info("Fetching channels for provider: %s, category: %s", provider, category)
    with open(CHANNELS_FILE % provider["path"], 'r') as f:
        channels = json.load(f)
    return channels[category["name"]]


def parse_iso8601(dtstr):
    try:
        return datetime.datetime.strptime(dtstr[:19], "%Y-%m-%dT%H:%M:%S")
    except Exception:
        return None


def get_current_epg(channel):
    """
    Return the current EPG entry for a PlutoTV channel, or None if not found.
    """
    now = datetime.datetime.utcnow()
    timelines = channel.get("timelines")
    if timelines:
        for programme in timelines:
            logger.info("programme: %s", programme)
            start = parse_iso8601(programme["start"])
            stop = parse_iso8601(programme["stop"])
            if start and stop and start <= now < stop:
                return programme
    return None


def get_upcoming_epg(channel):
    """
    Return a list of upcoming EPG entries for a PlutoTV channel.
    Each entry is a dict from the channel's 'timelines'.
    """
    logger.info("Fetching upcoming EPG for channel: %s", channel)
    now = datetime.datetime.utcnow()
    timelines = channel.get("timelines")
    if timelines:
        upcoming = []
        for programme in timelines:
            start = parse_iso8601(programme["start"])
            if start and start >= now:
                upcoming.append(programme)
        return upcoming
    return []
