import json
import typing as t
import typing_extensions as te
from .exceptions import LtiException


TSubmissionReview = te.TypedDict(
    "TSubmissionReview",
    {
        # Required data
        "reviewableStatus": t.List[str],
        # Optional data
        "label": str,
        "url": str,
        "custom": t.Dict[str, str],
    },
    total=False,
)

TLineItem = te.TypedDict(
    "TLineItem",
    {
        "id": str,
        "scoreMaximum": int,
        "label": str,
        "resourceId": str,
        "tag": str,
        "resourceLinkId": str,
        "startDateTime": str,
        "endDateTime": str,
        "gradesReleased": bool,
        # "submissionReview": TSubmissionReview,
    },
    total=False,
)
