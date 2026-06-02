import typing as t


# pylint: disable=too-few-public-methods, too-many-arguments
class Response:
    def __init__(
        self,
        result: t.Any,
        code: int,
        message: str,
        media_type: str = "application/json",
        problem_type: t.Optional[str] = None,
        headers: t.Optional[t.Dict[str, str]] = None,
    ) -> None:
        self.result = result
        self.code = code
        self.message = message
        self.media_type = media_type
        self.problem_type = problem_type
        self.headers: t.Dict[str, str] = headers or {}

    def set_media_type(self, media_type: str) -> None:
        self.media_type = media_type

    def set_header(self, key: str, value: str) -> None:
        self.headers[key] = value

    def append_header(self, key: str, value: str) -> None:
        if key in self.headers and self.headers[key]:
            self.headers[key] = f"{self.headers[key]}, {value}"
        else:
            self.headers[key] = value


def generate_link(link: str, rel: str) -> str:
    return f"<{link}>; rel={rel}"
