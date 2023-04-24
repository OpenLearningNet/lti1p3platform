from abc import ABC, abstractmethod
import typing as t
import typing_extensions as te
from functools import wraps
from .exceptions import LtiServiceException, LineItemNotFoundException
from .registration import Registration
from .lineitem import TLineItem
from .score import TScore, UpdateScoreStatus, UPDATE_SCORE_STATUSCODE
from .result import TResult
from .request import Request
from .ltiplatform import LTI1P3PlatformConfAbstract
from .ags import LtiAgs

TPage = te.TypedDict(
    "TPage",
    {
        "content": t.List[t.Any],
        "next": bool,
    },
)


def authenticate(
    allow_methods: t.Optional[t.List[str]] = None,
    accept: t.Optional[str] = None,
) -> None:
    def wrapper(func):
        def inner(service: "AssignmentsGradesService", *args, **kwargs):
            print(service, args, kwargs)
            auth = service._request.headers.get("Authorization", "").split()

            if not auth or auth[0].lower() != "bearer":
                raise LtiServiceException("Missing LTI 1.3 authentication token", 401)

            if len(auth) == 1:
                raise LtiServiceException("Invalid LTI 1.3 authentication token", 401)

            if len(auth) > 2:
                raise LtiServiceException("Invalid LTI 1.3 authentication token", 401)

            if allow_methods:
                if not service._request.method in allow_methods:
                    raise LtiServiceException(
                        "Method {} not allowed".format(service.request.method), 405
                    )

            if not service._platform_config.validate_token(
                auth[1], service.allowed_scopes
            ):
                raise LtiServiceException("Invalid LTI 1.3 authentication token", 401)

            resp = func(service, *args, **kwargs)
            if accept:
                resp.set_media_type(accept)

            return resp

        return inner

    return wrapper


class Response:
    def __init__(
        self,
        result: t.Any,
        code: int,
        message: str,
        media_type: str = "application/json",
        format: str = "json",
    ) -> None:
        self.result = result
        self.code = code
        self.message = message
        self.media_type = media_type
        self.format = format

    def set_media_type(self, media_type: str) -> None:
        self.media_type = media_type


class AssignmentsGradesService(ABC):
    _request = None
    _registration: t.Optional[Registration] = None

    def __init__(
        self,
        request: Request,
        platform_config: LTI1P3PlatformConfAbstract,
        lineitems_url: str,
        allow_creating_lineitems: bool,
        results_service_enabled: bool,
        scores_service_enabled: bool,
        **kwargs
    ) -> None:
        self._request = request
        self._platform_config = platform_config
        self._ags = LtiAgs(
            lineitems_url,
            None,
            allow_creating_lineitems,
            results_service_enabled,
            scores_service_enabled,
        )

    @property
    def allowed_scopes(self) -> t.List[str]:
        return self._ags.get_available_scopes()

    @abstractmethod
    # pylint: disable=too-many-arguments
    def find_lineitems(
        self,
        page: int = 1,
        limit: int = 10,
        line_item_id: t.Optional[str] = None,
        resource_link_id: t.Optional[str] = None,
        resource_id: t.Optional[str] = None,
        tag: t.Optional[str] = None,
    ) -> TPage:
        raise NotImplementedError()

    @abstractmethod
    def find_lineitem(self, line_item_id: str) -> TLineItem:
        raise NotImplementedError()

    @abstractmethod
    def create_lineitem(
        self,
        startDateTime: t.Optional[str] = None,
        endDateTime: t.Optional[str] = None,
        scoreMaximum: t.Optional[float] = None,
        label: t.Optional[str] = None,
        tag: t.Optional[str] = None,
        resourceLinkId: t.Optional[str] = None,
        resourceId: t.Optional[str] = None,
    ) -> TLineItem:
        raise NotImplementedError()

    @abstractmethod
    def update_lineitem(
        self,
        lineItemId: str,
        startDateTime: t.Optional[str] = None,
        endDateTime: t.Optional[str] = None,
        scoreMaximum: t.Optional[float] = None,
        label: t.Optional[str] = None,
        tag: t.Optional[str] = None,
        resourceLinkId: t.Optional[str] = None,
        resourceId: t.Optional[str] = None,
    ) -> TLineItem:
        raise NotImplementedError()

    @abstractmethod
    def delete_lineitem(
        self,
        line_item_id: str,
    ):
        raise NotImplementedError()

    @abstractmethod
    def update_score(self, line_item_id: str, score: TScore) -> UpdateScoreStatus:
        raise NotImplementedError()

    @abstractmethod
    def get_results(
        self, line_item_id: str, page: int, limit: int, user_id: t.Optional[str] = None
    ) -> t.List[TResult]:
        raise NotImplementedError()

    def handle_resp(self, func: t.Callable, **kwargs) -> Response:
        try:
            return func(**kwargs)
        except LtiServiceException as error:
            return Response(result=None, code=error.status_code, message=error.message)

    @authenticate(
        allow_methods=["GET"], accept="application/vnd.ims.lis.v2.resultcontainer+json"
    )
    def handle_get_results(self, line_item_id: str) -> t.List[TResult]:
        # The results service endpoint is a subpath of the line item
        # resource URL: it MUST be the line item resource URL with the
        # path appended with '/results'.
        lti_params = self._request.get_data

        try:
            results = self.get_results(line_item_id, **lti_params)
            return Response(result=results, code=200, message="success")
        except:
            return Response(result=None, code=404, message="Not found")

    @authenticate(
        allow_methods=["POST"], accept="application/vnd.ims.lis.v2.lineitem+json"
    )
    def handle_update_score(self, line_item_id: str) -> None:
        # The scores service endpoint is a subpath of the line item
        # resource URL: it MUST be the line item resource URL with the
        # path appended with '/scores'.
        score = self._request.json
        try:
            status = self.update_score(line_item_id, score)
            code = UPDATE_SCORE_STATUSCODE.get(status, 200)
            return Response(result=None, code=code, message=status.value)
        except LineItemNotFoundException:
            return Response(result=None, code=404, message="Not found")

    @authenticate(
        allow_methods=["GET"],
        accept="application/vnd.ims.lis.v2.lineitemcontainer+json",
    )
    def handle_get_lineitems(self) -> Response:
        lti_params = self._request.get_data

        lineitems = self.find_lineitems(**lti_params)
        return Response(
            result=lineitems,
            code=200,
            message="success",
        )

    @authenticate(
        allow_methods=["POST"], accept="application/vnd.ims.lis.v2.lineitem+json"
    )
    def handle_create_lineitem(self) -> Response:
        lineitem = self._request.json

        new_line_item = self.create_lineitem(**lineitem)
        return Response(result=new_line_item, code=201, message="success")

    @authenticate(
        allow_methods=["GET"], accept="application/vnd.ims.lis.v2.lineitem+json"
    )
    def handle_get_lineitem(self, line_item_id: str) -> Response:
        try:
            lineitem = self.find_lineitem_by_id(line_item_id=line_item_id)
            return Response(result=lineitem, code=200, message="success")
        except LineItemNotFoundException:
            return Response(result=None, code=404, message="Line item not found")

    @authenticate(
        allow_methods=["PUT"], accept="application/vnd.ims.lis.v2.lineitem+json"
    )
    def handle_update_lineitem(self, line_item_id: str) -> Response:
        try:
            updated_lineitem = self.update_lineitem(line_item_id, **self._request.json)
            return Response(result=updated_lineitem, code=200, message="success")
        except LineItemNotFoundException:
            return Response(result=None, code=404, message="Line item not found")

    @authenticate(allow_methods=["DELETE"])
    def handle_delete_lineitem(self, line_item_id: str) -> Response:
        try:
            self.delete_lineitem(line_item_id)

            return Response(result=None, code=204, message="success")
        except LineItemNotFoundException:
            return Response(result=None, code=404, message="Line item not found")
