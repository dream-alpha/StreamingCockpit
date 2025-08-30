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


import uuid
import json
import datetime
import urllib
import os
import urlparse
from .Debug import logger


CHANNEL_EPG_CACHE = "/etc/enigma2/plutotv-channel-epg-cache.json"


def get_url(channel):
    stitched_url = channel["stitched"]["urls"][0]["url"]
    parsed_url = urlparse.urlparse(stitched_url)
    params = urlparse.parse_qs(parsed_url.query)

    # Update existing parameters or add new ones
    device_id = str(uuid.uuid1())
    sid = str(uuid.uuid4())
    params.update(
        {
            "advertisingId": [""],
            "appName": ["web"],
            "appVersion": ["unknown"],
            "appStoreUrl": [""],
            "architecture": [""],
            "buildVersion": [""],
            "clientTime": ["0"],
            "deviceDNT": ["0"],
            "deviceId": [device_id],
            "deviceMake": ["Chrome"],
            "deviceModel": ["web"],
            "deviceType": ["web"],
            "deviceVersion": ["unknown"],
            "includeExtendedEvents": ["false"],
            "sid": [sid],
            "userId": [""],
            "serverSideAds": ["true"],
        }
    )

    query = urllib.urlencode(params, doseq=True)
    updated_url = urlparse.urlunparse((
        parsed_url.scheme,
        parsed_url.netloc,
        parsed_url.path,
        parsed_url.params,
        query,
        parsed_url.fragment
    ))
    return updated_url


def get_channels_dict():
    """
    Returns a dictionary of channels from the PlutoTV API.
    """
    logger.info("Reading channels dict...")
    if os.path.exists(CHANNEL_EPG_CACHE):
        with open(CHANNEL_EPG_CACHE, "r") as f:
            channels_dict = json.load(f)
        return channels_dict
    logger.error("Cache file not found.")
    return {"slugs": {}, "categories": {}}


def parse_iso8601(dtstr):
    # Python 2 doesn't have fromisoformat, so parse manually
    try:
        return datetime.datetime.strptime(dtstr[:19], "%Y-%m-%dT%H:%M:%S")
    except Exception:
        return None


def get_current_epg(slug):
    """
    Return the current EPG entry for a PlutoTV channel slug, or None if not found.
    """
    now = datetime.datetime.utcnow()
    timelines = slug.get("timelines")
    if timelines:
        for programme in timelines:
            logger.info("programme: %s", programme)
            start = parse_iso8601(programme["start"])
            stop = parse_iso8601(programme["stop"])
            if start and stop and start <= now < stop:
                return programme
    return None


def get_upcoming_epg(slug, limit=10):
    """
    Return a list of upcoming EPG entries for a PlutoTV channel slug.
    Each entry is a dict from the channel's 'timelines'.
    """
    logger.info("Fetching upcoming EPG for slug: %s", slug)
    now = datetime.datetime.utcnow()
    timelines = slug.get("timelines")
    if timelines:
        upcoming = []
        for programme in timelines:
            start = parse_iso8601(programme["start"])
            if start and start >= now:
                upcoming.append(programme)
                if len(upcoming) >= limit:
                    break
        return upcoming
    return []
