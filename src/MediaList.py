import os
from Components.config import config
from Components.Sources.List import List
from Tools.LoadPixmap import LoadPixmap
from .Debug import logger


def MediaEntryComponent(media, level):
    try:
        if level == 0:
            data_dir = config.plugins.streamingcockpit.providers_dir.value
        else:
            data_dir = config.plugins.streamingcockpit.data_dir.value
        png = None
        provider_id = media["provider_id"]
        thumbnail_name = media.get("thumbnail", None)
        thumbnail_file = os.path.join(data_dir, provider_id, thumbnail_name)
        logger.info("Loading thumbnail: %s", thumbnail_file)
        if thumbnail_file and os.path.isfile(thumbnail_file):
            png = LoadPixmap(thumbnail_file)
    except Exception as e:
        logger.error("Failed to load thumbnail: %s", e)

    title = media.get("title", "")
    if not title:
        title = media.get("name", "")
    return [
        media, title, media.get("description", ""), png
    ]

class MediaList(List):
    def __init__(self, alist, enableWrapAround=False):
        List.__init__(self, alist, enableWrapAround, item_height=50)
