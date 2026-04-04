from django.http import HttpResponse, HttpResponseRedirect
from lti1p3platform.oidc_login import OIDCLoginAbstract


class DjangoAPIOIDCLogin(OIDCLoginAbstract):
    def get_redirect(self, url: str) -> HttpResponseRedirect:
        return HttpResponseRedirect(url)

    def render_error_page(self, message: str, status_code: int) -> HttpResponse:
        return HttpResponse(message, status=status_code)
