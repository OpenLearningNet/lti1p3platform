import typing as t
import typing_extensions as te

TRequest = te.TypedDict(
    "TRequest",
    {
        "method": t.Optional[str],
        "form_data": t.Dict[str, t.Any],
        "get_data": t.Dict[str, t.Any],
        "headers": t.Mapping[str, t.Any],
        "content_type": t.Optional[str],
        "path": str,
        "json": t.Any,
    },
    total=False,
)


# T_aobj = t.TypeVar("T_aobj", bound="aobject")


# class aobject(object):
#     async def __new__(cls: t.Type[T_aobj], *args: t.Any, **kwargs: t.Any) -> T_aobj:
#         instance = super().__new__(cls)
#         instance.__init__(*args, **kwargs)
#         await instance.__ainit__()
#         return instance

#     @classmethod
#     async def new(cls: t.Type[T_aobj], *args: t.Any, **kwargs: t.Any) -> T_aobj:
#         instance = super().__new__(cls)
#         instance.__init__(*args, **kwargs)
#         await instance.__ainit__(*args, **kwargs)
#         return instance

#     def __init__(self, *args: t.Any, **kwargs: t.Any) -> None:
#         pass

#     async def __ainit__(self, *args: t.Any, **kwargs: t.Any) -> None:
#         pass


class RequestBase:
    request: TRequest

    @property
    def method(self) -> t.Optional[str]:
        return self.request["method"]

    @property
    def form_data(self) -> t.Dict[str, t.Any]:
        return self.request["form_data"]

    @property
    def get_data(self) -> t.Dict[str, t.Any]:
        return self.request["get_data"]

    @property
    def headers(self) -> t.Mapping[str, t.Any]:
        return self.request["headers"]

    @property
    def content_type(self) -> t.Optional[str]:
        return self.request["content_type"]

    @property
    def path(self) -> str:
        return self.request["path"]

    @property
    def json(self) -> t.Any:
        return self.request["json"]


class Request(RequestBase):
    def __init__(self, request: t.Any) -> None:
        self.request = self.build_metadata(request)

    def build_metadata(self, request: t.Any) -> TRequest:
        raise NotImplementedError


# class AsyncRequest(RequestBase, aobject):
#     async def __ainit__(self, request: t.Any) -> None:
#         self.request = await self.build_metadata(request)

#     async def build_metadata(self, request: t.Any) -> TRequest:
#         raise NotImplementedError
