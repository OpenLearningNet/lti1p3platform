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


TScore = te.TypedDict(
    "TScore",
    {
        "userId": int,
        "scoreGiven": float,
        "scoreMaximum": float,
        "comment": str,
        "timestamp": datetime,
        "activityProgress": ActivityProgress,
        "gradingProgress": GradeProgress,
    },
    total=False,
)
