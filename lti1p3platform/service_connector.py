from abc import ABC, abstractmethod
import typing as t
from functools import wraps
from .exceptions import LtiServiceException
from .registration import Registration
from .lineitem import TLineItem
from .score import TScore
from .result import TResult
from .request import Request


def authenticate(
    func: t.Callable,
    allow_methods: t.Optional[t.List[str]] = None,
    accept: t.Optional[str] = None,
) -> None:
    @wraps(func)
    def wrapper(service: "AssignmentsGradesService", *args, **kwargs):
        auth = service.request.headers.get("Authorization", "").split()

        if not auth or auth[0].lower() != "bearer":
            raise LtiServiceException("Missing LTI 1.3 authentication token", 401)

        if len(auth) == 1:
            raise LtiServiceException("Invalid LTI 1.3 authentication token", 401)

        if len(auth) > 2:
            raise LtiServiceException("Invalid LTI 1.3 authentication token", 401)

        if allow_methods:
            if not service.request.method in allow_methods:
                raise LtiServiceException(
                    "Method {} not allowed".format(service.request.method), 405
                )

        if accept:
            if not service.request.content_type == accept:
                raise LtiServiceException(
                    "Content type {} not allowed".format(service.request.content_type),
                    406,
                )

        return func(*args, **kwargs)

    return wrapper


class AssignmentsGradesService(ABC):
    _request = None
    _registration: t.Optional[Registration] = None

    def __init__(self, request: Request, **kwargs) -> None:
        self._request = request

    @abstractmethod
    # pylint: disable=too-many-arguments
    def find_lineitems(
        self,
        line_item_id: t.Optional[str] = None,
        resource_link_id: t.Optional[str] = None,
        resource_id: t.Optional[str] = None,
        tag: t.Optional[str] = None,
        limit: t.Optional[int] = None,
    ) -> t.List[TLineItem]:
        raise NotImplementedError()

    @authenticate(
        allow_methods=["GET"], accept="application/vnd.ims.lis.v2.resultcontainer+json"
    )
    def handle_get_results(self, line_item_id: str) -> t.List[TResult]:
        # The results service endpoint is a subpath of the line item
        # resource URL: it MUST be the line item resource URL with the
        # path appended with '/results'.

        pass

    @authenticate(allow_methods=["POST"])
    def handle_update_scores(self) -> None:
        # The scores service endpoint is a subpath of the line item
        # resource URL: it MUST be the line item resource URL with the
        # path appended with '/scores'.
        pass

    @authenticate(allow_methods=["GET"])
    def handle_get_lineitems(self) -> t.List[TLineItem]:
        lti_params = self.get_data()

        lineitems = self.find_lineitems(**lti_params)
        return lineitems

    @authenticate(allow_methods=["GET"])
    def handle_get_lineitem(self, line_item_id: str) -> TLineItem:
        content_type = self.get_content_type()

        if content_type != "application/vnd.ims.lis.v2.lineitem+json":
            raise LtiServiceException("Invalid content type", 400)

        try:
            return self.find_lineitems(line_item_id=line_item_id)[0]
        except KeyError as err:
            raise LtiServiceException("Line item not found", 404) from err

    @authenticate(allow_methods=["PUT", "POST"])
    def handle_update_lineitem(self) -> None:
        pass

    @authenticate(allow_methods=["DELETE"])
    def handle_delete_lineitem(self, line_item_id: str) -> None:
        pass
