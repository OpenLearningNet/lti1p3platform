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
    ) -> None:
        self.result = result
        self.code = code
        self.message = message
        self.media_type = media_type
        self.problem_type = problem_type

    def set_media_type(self, media_type: str) -> None:
        self.media_type = media_type


def generate_next_link(link: str) -> str:
    return f"<{link}>; rel=next"
