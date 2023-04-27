# from fastapi import Request as OriginRequest
# from lti1p3platform.request import AsyncRequest, TRequest


# class FastApiRequest(AsyncRequest):
#     async def build_metadata(self, request: OriginRequest) -> TRequest:
#         form_data = await request.form()
#         json_data = (
#             await request.json()
#             if request.headers.get("content-type") == "application/json"
#             else ""
#         )

#         return {
#             "method": request.method,
#             "form_data": form_data._dict,
#             "get_data": request.query_params._dict,
#             "headers": request.headers,
#             "content_type": request.headers.get("content-type"),
#             "path": request.url.path,
#             "json": json_data,
#         }
