import typing as t
import typing_extensions as te

from .lineitem import TDeepLinkingLineItem

# http://www.imsglobal.org/spec/lti-dl/v2p0#content-item-types
TURL = te.TypedDict(
    "TURL",
    {
        "url": str,
        "width": int,
        "height": int,
    },
    total=False,
)

TWindow = te.TypedDict(
    "TWindow",
    {
        "targetName": str,
        "width": int,
        "height": int,
        "windowFeatures": t.List[str],
    },
    total=False,
)

TIFrame = te.TypedDict(
    "TIFrame",
    {
        "src": str,
        "width": int,
        "height": int,
    },
    total=False,
)

TLink = te.TypedDict(
    "TLink",
    {
        "title": str,
        "url": str,
        "text": str,
        "icon": TURL,
        "thumbnail": TURL,
        "embed": str,
        "window": TWindow,
        "iframe": TIFrame,
    },
    total=False,
)

TTimeDelta = te.TypedDict(
    "TTimeDelta",
    {
        "startDateTime": str,
        "endDateTime": str,
    },
    total=False,
)

TLtiResourceLink = te.TypedDict(
    "TLtiResourceLink",
    {
        "url": str,
        "title": str,
        "text": str,
        "icon": TURL,
        "thumbnail": TURL,
        "window": TWindow,
        "iframe": TIFrame,
        "custom": t.Dict[str, str],
        "lineItem": TDeepLinkingLineItem,
        "available": TTimeDelta,
        "submission": TTimeDelta,
    },
    total=False,
)

TFile = te.TypedDict(
    "TFile",
    {
        "url": str,
        "title": str,
        "text": str,
        "icon": TURL,
        "thumbnail": TURL,
        "expiresAt": str,
    },
    total=False,
)

THtml = te.TypedDict(
    "THtml",
    {
        "html": str,
        "title": str,
        "text": str,
    },
    total=False,
)

TImage = te.TypedDict(
    "TImage",
    {
        "url": str,
        "title": str,
        "text": str,
        "icon": TURL,
        "thumbnail": TURL,
        "width": int,
        "height": int,
    },
    total=False,
)

LTI_DEEP_LINKING_CONTENT_ITEM_TYPE = {
    "link": TLink,
    "ltiResourceLink": TLtiResourceLink,
    "file": TFile,
    "html": THtml,
    "image": TImage,
}
