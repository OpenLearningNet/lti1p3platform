from fastapi.responses import PlainTextResponse, RedirectResponse
from lti1p3platform.oidc_login import OIDCLoginAbstract


class FastAPIOIDCLogin(OIDCLoginAbstract):
    def get_redirect(self, url: str) -> RedirectResponse:
        return RedirectResponse(url)

    def render_error_page(self, message: str, status_code: int) -> PlainTextResponse:
        return PlainTextResponse(message, status_code=status_code)
