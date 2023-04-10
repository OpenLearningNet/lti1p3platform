from fastapi import Request
from lti1p3platform.request import Request, TRequest


class FastApiRequest(Request):
    def build_metadata(self, request: Request) -> TRequest:
        return {
            "method": request.method,
            "post_data": request.form,
            "get_data": request.query_params,
            "headers": request.headers,
            "content_type": request.headers.get("content-type"),
            "path": request.url.path,
        }
