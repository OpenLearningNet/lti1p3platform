from django.http import JsonResponse
from lti1p3platform.service_connector import Response


def wrap_json_resp(resp: Response) -> JsonResponse:
    if 200 <= resp.code < 300:
        if resp.result and "content" in resp.result:
            data = resp.result["content"]
        else:
            data = resp.result

        response = JsonResponse(
            data, status=resp.code, content_type=resp.media_type, safe=False
        )

        if resp.result and "next" in resp.result and resp.result["next"]:
            response.headers["Link"] = resp.result["next"] + "; rel=next"

        return response
    else:
        return JsonResponse(
            {"error": resp.message}, status=resp.code, content_type=resp.media_type
        )
