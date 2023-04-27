from abc import ABC, abstractmethod
import typing as t
from urllib.parse import urlencode
import typing_extensions as te

from .exceptions import LtiServiceException, LineItemNotFoundException
from .lineitem import TLineItem
from .score import TScore, UpdateScoreStatus, UPDATE_SCORE_STATUSCODE
from .request import Request
from .response import Response
from .ltiplatform import LTI1P3PlatformConfAbstract
from .ags import LtiAgs

TPage = te.TypedDict(
    "TPage",
    {
        "content": t.List[t.Any],
        "has_next": bool,
        "next": t.Optional[str],
    },
    total=False,
)

F = t.TypeVar("F", bound=t.Callable[..., Response])


def authenticate(
    allow_methods: t.Optional[t.List[str]] = None,
    accept: t.Optional[str] = None,
) -> t.Callable[[F], t.Callable[["AssignmentsGradesService", t.Any, t.Any], Response]]:
    def wrapper(
        func: F,
    ) -> t.Callable[["AssignmentsGradesService", t.Any, t.Any], Response]:
        def inner(
            service: "AssignmentsGradesService", *args: t.Any, **kwargs: t.Any
        ) -> Response:
            assert service.request

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
                        f"Method {service.request.method} not allowed", 405
                    )

            if not service.platform_config.validate_token(
                auth[1], service.allowed_scopes
            ):
                raise LtiServiceException("Invalid LTI 1.3 authentication token", 401)

            resp = func(service, *args, **kwargs)
            if accept:
                resp.set_media_type(accept)

            return resp

        return inner

    return wrapper


class AssignmentsGradesService(ABC):
    request = None

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        request: Request,
        platform_config: LTI1P3PlatformConfAbstract,
        lineitems_url: str,
        lineitem_url: t.Optional[str] = None,
        allow_creating_lineitems: bool = True,
        results_service_enabled: bool = True,
        scores_service_enabled: bool = True,
    ) -> None:
        self.request = request
        self.platform_config = platform_config
        self.ags = LtiAgs(
            lineitems_url.rstrip("/"),
            lineitem_url.rstrip("/") if lineitem_url else None,
            allow_creating_lineitems,
            results_service_enabled,
            scores_service_enabled,
        )

    @property
    def allowed_scopes(self) -> t.List[str]:
        return self.ags.get_available_scopes()

    @abstractmethod
    # pylint: disable=too-many-arguments
    def find_lineitems(
        self,
        page: int = 1,
        limit: t.Optional[int] = None,
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
        creation_data: TLineItem,
    ) -> TLineItem:
        raise NotImplementedError()

    @abstractmethod
    def update_lineitem(
        self,
        update_data: TLineItem,
    ) -> TLineItem:
        raise NotImplementedError()

    @abstractmethod
    def delete_lineitem(
        self,
        line_item_id: str,
    ) -> None:
        raise NotImplementedError()

    @abstractmethod
    def update_score(self, line_item_id: str, score: TScore) -> UpdateScoreStatus:
        raise NotImplementedError()

    @abstractmethod
    def get_results(
        self,
        line_item_id: str,
        page: int = 1,
        limit: t.Optional[int] = None,
        user_id: t.Optional[str] = None,
    ) -> TPage:
        raise NotImplementedError()

    def handle_resp(self, func: t.Callable[..., Response], **kwargs: t.Any) -> Response:
        try:
            return func(**kwargs)
        except LtiServiceException as error:
            return Response(result=None, code=error.status_code, message=error.message)

    @authenticate(
        allow_methods=["GET"], accept="application/vnd.ims.lis.v2.resultcontainer+json"
    )
    def handle_get_results(self, line_item_id: str) -> Response:
        # The results service endpoint is a subpath of the line item
        # resource URL: it MUST be the line item resource URL with the
        # path appended with '/results'.
        assert self.request is not None

        lti_params = self.request.get_data

        try:
            results = self.get_results(line_item_id, **lti_params)

            if results["has_next"]:
                page = lti_params.get("page", 1)
                lti_params["page"] = page + 1

                results[
                    "next"
                ] = f"{self.ags.lineitem_url}/results?{urlencode(lti_params)}"

            return Response(result=results, code=200, message="success")
        except LineItemNotFoundException:
            return Response(result=None, code=404, message="Not found")

    @authenticate(
        allow_methods=["POST"], accept="application/vnd.ims.lis.v2.lineitem+json"
    )
    def handle_update_score(self, line_item_id: str) -> Response:
        # The scores service endpoint is a subpath of the line item
        # resource URL: it MUST be the line item resource URL with the
        # path appended with '/scores'.
        assert self.request is not None

        score = self.request.json

        # TODO: validate score
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
        assert self.request is not None

        lti_params = self.request.get_data

        lineitems = self.find_lineitems(**lti_params)
        if lineitems["has_next"]:
            page = lti_params.get("page", 1)
            lti_params["page"] = page + 1

            lineitems["next"] = f"{self.ags.lineitems_url}?{urlencode(lti_params)}"

        return Response(
            result=lineitems,
            code=200,
            message="success",
        )

    @authenticate(
        allow_methods=["POST"], accept="application/vnd.ims.lis.v2.lineitem+json"
    )
    def handle_create_lineitem(self) -> Response:
        assert self.request is not None

        lineitem = self.request.json

        new_line_item = self.create_lineitem(t.cast(TLineItem, lineitem))
        return Response(result=new_line_item, code=201, message="success")

    @authenticate(
        allow_methods=["GET"], accept="application/vnd.ims.lis.v2.lineitem+json"
    )
    def handle_get_lineitem(self, line_item_id: str) -> Response:
        try:
            lineitem = self.find_lineitem(line_item_id=line_item_id)
            return Response(result=lineitem, code=200, message="success")
        except LineItemNotFoundException:
            return Response(result=None, code=404, message="Line item not found")

    @authenticate(
        allow_methods=["PUT"], accept="application/vnd.ims.lis.v2.lineitem+json"
    )
    def handle_update_lineitem(self, line_item_id: str) -> Response:
        assert self.request is not None

        try:
            update_data = self.request.json
            update_data.update({"id": line_item_id})
            updated_lineitem = self.update_lineitem(t.cast(TLineItem, update_data))
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
