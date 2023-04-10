import typing_extensions as te

TResult = te.TypedDict(
    "TResult",
    {
        "id": str,
        "userId": int,
        "resultScore": float,
        "resultMaximum": float,
        "comment": str,
        "scoreOf": str,
    },
    total=False,
)
