import typing as t
from dataclasses import asdict, is_dataclass


def dataclass_to_dict(obj: t.Any) -> t.Any:
    if is_dataclass(obj):
        return {k: dataclass_to_dict(v) for k, v in asdict(obj).items()}

    if isinstance(obj, dict):
        return {k: dataclass_to_dict(v) for k, v in obj.items()}

    if isinstance(obj, (list, tuple, set)):
        # pylint: disable=no-value-for-parameter
        return type(obj)(dataclass_to_dict(v) for v in obj)

    return obj
