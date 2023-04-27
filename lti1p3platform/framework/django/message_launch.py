import typing as t

from django.http import HttpRequest, HttpResponse

from lti1p3platform.message_launch import LTIAdvantageMessageLaunchAbstract
from lti1p3platform.ltiplatform import LTI1P3PlatformConfAbstract

from ..templates import template
from .request import DjangoRequest


class DjangoLTI1P3MessageLaunch(LTIAdvantageMessageLaunchAbstract):
    def __init__(
        self, request: DjangoRequest, platform_config: LTI1P3PlatformConfAbstract
    ) -> None:
        assert isinstance(
            request, DjangoRequest
        ), "Request is not instance of DjangoRequest"

        super().__init__(request, platform_config)

    def render_launch_form(
        self, launch_data: t.Dict[str, t.Any], **kwargs: t.Any
    ) -> HttpResponse:
        return HttpResponse(template.render(launch_data))
