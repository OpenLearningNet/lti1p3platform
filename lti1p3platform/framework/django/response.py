from django.http import JsonResponse
from http import HTTPStatus
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
        try:
            title = HTTPStatus(resp.code).phrase
        except ValueError:
            title = "Error"

        problem_type = resp.problem_type or "about:blank"

        return JsonResponse(
            {
                "type": problem_type,
                "title": title,
                "status": resp.code,
                "detail": resp.message,
            },
            status=resp.code,
            content_type="application/problem+json",
        )
