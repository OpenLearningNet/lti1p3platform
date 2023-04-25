<!-- @format -->

# LTI 1.3 Platform implementation in Python

# Usage

## Register your platform

The platform should prepare the launch by gathering the necessary context information, including details about the user, the course, and any custom parameters that need to be included in the launch request.

```python
from lti1p3platform.ltiplatform import LTI1P3PlatformConfAbstract
from lti1p3platform.registration import Registration

class LTIPlatformConf(LTI1P3PlatformConfAbstract):
    def init_platform_config(self, platform_settings, platform_key_set):
        """
        register platform configuration
        """
        registration = Registration() \
            .set_client_id(platform_settings.client_id) \
            .set_deployment_id(platform_settings.deployment_id) \
            .set_launch_url(platform_settings.launch_url) \
            .set_deeplink_launch_url(platform_settings.deeplink_launch_url) \
            .set_oidc_login_url(platform_settings.oidc_login_url) \
            .set_tool_key_set_url(platform_settings.key_set_url) \
            .set_platform_public_key(platform_key_set.public_key) \
            .set_platform_private_key(platform_key_set.private_key)

        self._registration = registration

def get_registered_platform(*args, **kwargs):
    ...

    return LTIPlatformConf(*args, **kwargs)

# public JWK endpoint
def get_jwks(request, *args, **kwargs):
    platform = get_registered_platform(*args, **kwargs)

    return HttpResponseJSON(platform.get_jwks())
```

## OIDC initiate login

The tool consumer (i.e., the LMS) sends a request to the tool provider's application to initiate the OIDC authentication flow.

```python
from lti1p3platform.oidc_login import OIDCLoginAbstract

class OIDCLogin(OIDCLoginAbstract):
    def set_lti_message_hint(self, **kwargs):
        """ set your own lti_message_hint """
        pass

    def get_lti_message_hint(self):
        """ get your lti_message_hint """
        pass

    def get_redirect(self, url):
        """
        This will be invoked in initiate_login, and it depends on which web framework you are using.
        Here is an example for Django framework:
        """
        return HttpResponseRedirect(url)

# Initiate login endpoint
def preflight_lti_1p3_launch(request, user_id, *args, **kwargs):
    platform = get_registered_platform(*args, **kwargs)
    oidc_login = OLOIDCLogin(request, platform)

    # Redirect the current login user to the tool provider,
    return redirect_url.initiate_login(user_id)

```

## LTI Message launch

The tool provider redirect to the platform's OIDC auth request endpoint. The platform received the auth request and it will do some little bit of validation, it needs to ensure user is login, also check the `login_hint` is matched with the `user_id`. The platform also could get the context from the `lti_message_hint` which is sent in the initiating request and do some other validation.

After all verifications, the platform will generate a `id_token`. The platform encodes all important launch message payload as a JWT and send it as `id_token` parameter in a post request to the tool launch url.

```python
from lti1p3platform.message_launch import MessageLaunchAbstract

class LTI1p3MessageLaunch(MessageLaunchAbstract):
    def render_launch_form(self, launch_data, **kwargs):
        """
        This will be invoked in the last step of `lti_launch`.
        So you could render a template in this method. This template should render a form, and then submit it to the tool's launch URL. There is a django example in framework/django/message_launch.py
        """
        pass

    def prepare_launch(self, preflight_response, **kwargs):
        """
        You could do some other checks and get some contexts from `lti_message_hint` you've set in previous request
        Also you could call these methods to prepare your own jwt payload:
            - set_user_data
            - set_resource_link_claim
            - set_launch_context_claim
            - set_custom_parameters_claim

        Make sure do these things before lti_launch, it could send necessary launch parameters to the tool.
        """
        pass

def lti_resource_link_launch(request, *args, **kwargs):
    platform = get_registered_platform(*args, **kwargs)
    message_launch = LTI1p3MessageLaunch(request, *args, **kwargs)

    return launch.lti_launch(*args, **kwargs)
```

## Examples

[Django example](examples/django_platform/README.md)

# Development

## Run test

Prerequisite: tox and python 3.7, 3.8, 3.9, 3.10

If you are using pyenv virtualenv, you might need to install all python versions and run `pyenv local 3.7.x 3.8.x 3.9.x 3.10.x` at the first time.

```bash
cd lti1p3platform
tox
```
