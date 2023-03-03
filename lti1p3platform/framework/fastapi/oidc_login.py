from fastapi import RedirectResponse
from lti1p3platform.oidc_login import OIDCLoginAbstract

class FastAPIOIDCLogin(OIDCLoginAbstract):
    def get_redirect(self, url):
        return RedirectResponse(url)
