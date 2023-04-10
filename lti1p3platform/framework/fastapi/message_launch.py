import typing as t

from fastapi.requests import Request
from fastapi.responses import Response

from lti1p3platform.message_launch import MessageLaunchAbstract

from ..templates import template


class FastapiMessageLaunch(MessageLaunchAbstract):
    def get_preflight_response(self) -> t.Dict[str, t.Any]:
        assert isinstance(self._request, Request), "Request is not instance of Request"

        # pylint: disable=protected-access
        return self._request.query_params._dict

    def render_launch_form(
        self, launch_data: t.Dict[str, t.Any], **kwargs: t.Any
    ) -> Response:
        return Response(template.render(launch_data))
