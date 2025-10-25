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
import json
from Tools.Directories import resolveFilename, SCOPE_CONFIG
from .Debug import logger

config_dir = resolveFilename(SCOPE_CONFIG)
config_file = os.path.join(config_dir, "stc_config.json")


class STC_Config:
    def __init__(self):
        pass

    def get_index(self, config, provider_id, level):
        logger.info("config: %s, provider_id: %s, level: %s", config, provider_id, level)
        if level == 0:
            provider_id = "root"
        provider = config.get(provider_id, {})
        return provider.get(str(level), 0)

    def set_index(self, config, provider_id, level, index):
        logger.info("config: %s, provider_id: %s, level: %s, index: %s", config, provider_id, level, index)
        if level == 0:
            provider_id = "root"
        if provider_id not in config:
            config[provider_id] = {}
        config[provider_id][str(level)] = index

    def load(self):
        config = {}
        if os.path.exists(config_file):
            try:
                with open(config_file, "r") as f:
                    config = json.load(f)
            except (ValueError, IOError):
                config = {}
        logger.info("config: %s", config)
        return config

    def save(self, config):
        logger.info("config: %s, config_file: %s", config, config_file)
        try:
            with open(config_file, "w") as f:
                json.dump(config, f, indent=4)
        except (TypeError, IOError):
            pass
        logger.info("config: %s", config)
