import json

from django.http import HttpRequest
from lti1p3platform.request import Request, TRequest


class DjangoRequest(Request):
    def build_metadata(self, request: HttpRequest) -> TRequest:
        assert isinstance(request, HttpRequest)

        json_data = None

        if request.body and request.content_type and "json" in request.content_type:
            json_data = json.loads(request.body)

        return {
            "method": request.method,
            "form_data": request.POST.dict(),
            "json": json_data,
            "get_data": request.GET.dict(),
            "headers": request.headers,
            "content_type": request.content_type,
            "path": request.path,
        }
