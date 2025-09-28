from Components.Sources.List import List
from Tools.Directories import resolveFilename, SCOPE_SKIN_IMAGE
from Tools.LoadPixmap import LoadPixmap
from .Debug import logger


def MediaEntryComponent(media):

    icon = media.get("icon", None)
    if icon is None:
        icon_file = resolveFilename(SCOPE_SKIN_IMAGE, "skin_default/icons/media.png")
    else:
        icon_file = resolveFilename(SCOPE_SKIN_IMAGE, "skin_default/icons/" + icon)
    try:
        png = LoadPixmap(icon_file)
    except Exception as e:
        logger.error("Failed to load icon: %s", e)
        png = None

    return [
        media, str(media.get("name", "")), str(media.get("description", "")), png
    ]

class MediaList(List):
    def __init__(self, alist, enableWrapAround=False):
        List.__init__(self, alist, enableWrapAround, item_height=50)
