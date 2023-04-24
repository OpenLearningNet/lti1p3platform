import typing_extensions as te

# https://www.imsglobal.org/spec/lti-ags/v2p0/#media-type-and-schema
TResult = te.TypedDict(
    "TResult",
    {
        "id": str,  # URL uniquely identifying the result record.
        "userId": int,  # LTI user ID identifying the recipient of the Result
        "resultScore": float,  # The current score for this user.
        "resultMaximum": float,  # The 'resultMaximum' value MUST be a positive number (with 0 considered a negative number); if no value is specified, then a default maximum value of 1 must be used.
        "comment": str,  # The value must be a string. If no value exists, this attribute may be omitted, blank or have an explicit null value.
        "scoreOf": str,  # URL identifying the Line Item to which this result belongs.
    },
    total=False,
)
