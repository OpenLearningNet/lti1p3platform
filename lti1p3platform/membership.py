import typing as t
from enum import Enum
from dataclasses import dataclass


class Status(Enum):
    ACTIVE = "Active"
    DELETED = "Deleted"
    INACTIVE = "Inactive"


@dataclass
class Context:
    id: str
    label: str
    title: str


@dataclass
class ContextMembership:
    id: str
    context: Context


@dataclass
class ResourceLinkMembership(ContextMembership):
    message: t.List[t.Dict[str, t.Any]]
