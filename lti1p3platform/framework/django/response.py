from django.http import JsonResponse
from http import HTTPStatus
from lti1p3platform.response import Response, generate_link


def wrap_json_resp(resp: Response) -> JsonResponse:
    if 200 <= resp.code < 300:
        if resp.result and "content" in resp.result:
            data = resp.result["content"]
        else:
            data = resp.result

        response = JsonResponse(
            data, status=resp.code, content_type=resp.media_type, safe=False
        )

        for key, value in resp.headers.items():
            response.headers[key] = value

        if resp.result and "next" in resp.result and resp.result["next"]:
            next_link = generate_link(resp.result["next"], "next")
            if response.headers.get("Link"):
                if next_link not in response.headers["Link"]:
                    response.headers[
                        "Link"
                    ] = f"{response.headers['Link']}, {next_link}"
            else:
                response.headers["Link"] = next_link

        if resp.result and "differences" in resp.result and resp.result["differences"]:
            differences_link = generate_link(resp.result["differences"], "differences")
            if response.headers.get("Link"):
                if differences_link not in response.headers["Link"]:
                    response.headers[
                        "Link"
                    ] = f"{response.headers['Link']}, {differences_link}"
            else:
                response.headers["Link"] = differences_link

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
