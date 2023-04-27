from enum import Enum
from datetime import datetime
import typing_extensions as te


class ActivityProgress(Enum):
    INITIALIZED = "Initialized"
    STARTED = "Started"
    INPROGRESS = "InProgress"
    SUBMITTED = "Submitted"
    COMPLETED = "Completed"


class GradeProgress(Enum):
    NOTREADY = "NotReady"
    PENDING = "Pending"
    FAILED = "Failed"
    PENDINGMANUAL = "PendingManual"
    FULLYGRADED = "FullyGraded"


class UpdateScoreStatus(Enum):
    # Successful operation, score update has been received.
    SUCCESS = "success"
    # Successful operation, score update has been received.
    # A new result was created.
    CREATED = "created"
    # The server has accepted the request, but the processing
    # is not complete.
    PENDING = "pending"
    # The server has accepted the request, but the score was
    # not applied.
    NOTAPPLIED = "notapplied"

    # The Score has an earlier timestamp than the last one
    # successfully processed
    OLD_TIMESTAMP = "oldtimestamp"


UPDATE_SCORE_STATUSCODE = {
    UpdateScoreStatus.CREATED: 201,
    UpdateScoreStatus.SUCCESS: 200,
    UpdateScoreStatus.PENDING: 202,
    UpdateScoreStatus.NOTAPPLIED: 403,
    UpdateScoreStatus.OLD_TIMESTAMP: 409,
}

# https://www.imsglobal.org/spec/lti-ags/v2p0/#score-service-media-type-and-schema
TSubmission = te.TypedDict(
    "TSubmission",
    {
        "startedAt": datetime,
        "submittedAt": datetime,
    },
    total=False,
)

TScore = te.TypedDict(
    "TScore",
    {
        "userId": int,  # LTI user ID identifying the recipient of the Result
        "scoreGiven": float,
        "scoreMaximum": float,
        "comment": str,
        "timestamp": datetime,
        "activityProgress": ActivityProgress,
        "gradingProgress": GradeProgress,
        "submission": TSubmission,
    },
    total=False,
)
