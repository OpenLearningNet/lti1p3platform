from django.http import HttpResponseRedirect
from lti1p3platform.oidc_login import OIDCLoginAbstract


class DjangoAPIOIDCLogin(OIDCLoginAbstract):
    def get_redirect(self, url: str) -> HttpResponseRedirect:
        return HttpResponseRedirect(url)
