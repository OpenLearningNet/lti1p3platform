from django.http import JsonResponse
from lti1p3platform.response import Response, generate_next_link


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
            response.headers["Link"] = generate_next_link(resp.result["next"])

        return response
    else:
        return JsonResponse(
            {"error": resp.message}, status=resp.code, content_type=resp.media_type
        )
