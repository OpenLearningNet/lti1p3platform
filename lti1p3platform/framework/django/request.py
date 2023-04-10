from django.http import HttpRequest
from lti1p3platform.request import Request, TRequest


class DjangoRequest(Request):
    def build_metadata(self, request: HttpRequest) -> TRequest:
        assert isinstance(request, HttpRequest)

        return {
            "method": request.method,
            "post_data": request.POST.dict(),
            "get_data": request.GET.dict(),
            "headers": request.headers,
            "content_type": request.content_type,
            "path": request.path,
        }
