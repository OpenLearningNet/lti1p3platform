from abc import ABC, abstractmethod
import typing as t
import typing_extensions as te

TRequest = te.TypedDict(
    "TRequest",
    {
        "method": str,
        "post_data": t.Dict[str, t.Any],
        "get_data": t.Dict[str, t.Any],
        "headers": t.Dict[str, t.Any],
        "content_type": str,
        "path": str,
    },
    total=False,
)


class Request(ABC):
    request: TRequest

    def __init__(self, request: t.Any):
        self.request = self.build_metadata(request)

    @abstractmethod
    def build_metadata(self, request: t.Any) -> TRequest:
        pass

    @property
    def method(self) -> str:
        return self.request["method"]

    @property
    def post_data(self) -> t.Dict[str, t.Any]:
        return self.request["post_data"]

    @property
    def get_data(self) -> t.Dict[str, t.Any]:
        return self.request["get_data"]

    @property
    def headers(self) -> t.Dict[str, t.Any]:
        return self.request["headers"]

    @property
    def content_type(self) -> str:
        return self.request["content_type"]

    @property
    def path(self) -> str:
        return self.request["path"]
