import typing as t

from django.http import HttpRequest, HttpResponse

from lti1p3platform.message_launch import MessageLaunchAbstract

from ..templates import template


class DjangoLTI1P3MessageLaunch(MessageLaunchAbstract):
    def get_preflight_response(self) -> t.Dict[str, t.Any]:
        assert isinstance(
            self._request, HttpRequest
        ), "Request is not instance of HttpRequest"

        return self._request.GET.dict() or self._request.POST.dict()

    def render_launch_form(
        self, launch_data: t.Dict[str, t.Any], **kwargs: t.Any
    ) -> HttpResponse:
        return HttpResponse(template.render(launch_data))
