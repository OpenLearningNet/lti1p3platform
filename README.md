<!-- @format -->

# LTI 1.3 Platform implementation in Python

# Installation

Install the core library only:

```bash
pip install lti1p3platform
```

Install with Django support:

```bash
pip install lti1p3platform[Django]
```

Install with FastAPI support:

```bash
pip install lti1p3platform[fastapi]
```

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
            .set_platform_private_key(platform_key_set.private_key) \
            .set_tool_redirect_uris([
                "https://tool.example.com/lti/launch",
                "https://tool.example.com/lti/deeplink",
            ])

        self._registration = registration

def get_registered_platform(*args, **kwargs):
    ...

    return LTIPlatformConf(*args, **kwargs)

# public JWK endpoint
def get_jwks(request, *args, **kwargs):
    platform = get_registered_platform(*args, **kwargs)

    return HttpResponseJSON(platform.get_jwks())
```

> **Important – redirect URI allowlist:** `set_tool_redirect_uris()` is required.
> It defines the allowlist of redirect URIs that the tool is permitted to supply
> during an OIDC/LTI launch. The `redirect_uri` sent by the tool in the preflight
> response must exactly match one of the registered values, otherwise the launch
> will fail with an `invalid_request_uri` error and render a local error page
> (not a redirect). All URIs must use HTTPS; plain HTTP is only accepted for
> `localhost` / `127.0.0.1` / `::1` during development.

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

    def render_error_page(self, message, status_code):
        """
        This will be invoked when the library decides the error must not be
        returned as an OAuth redirect.
        """
        return HttpResponse(message, status=status_code)

# Initiate login endpoint
def preflight_lti_1p3_launch(request, user_id, *args, **kwargs):
    platform = get_registered_platform(*args, **kwargs)
    oidc_login = OIDCLogin(request, platform)

    # Redirect the current login user to the tool provider,
    return oidc_login.initiate_login(user_id)

```

### OIDC error response behavior

The library decides whether an OIDC/login error should be returned as a redirect
to the tool or rendered locally as an error page.

| Scenario | Error code | Behavior |
|----------|------------|----------|
| Unknown `client_id` | `unauthorized_client` | Redirect to `redirect_uri` with OAuth error params |
| Missing required params | `invalid_request` | Redirect to `redirect_uri` with OAuth error params |
| Wrong `response_type` | `unsupported_response_type` | Redirect to `redirect_uri` with OAuth error params |
| Missing `openid` scope | `invalid_scope` | Redirect to `redirect_uri` with OAuth error params |
| Bad `login_hint` | `invalid_request` | Redirect to `redirect_uri` with OAuth error params |
| Expired `lti_message_hint` | `invalid_request` | Redirect to `redirect_uri` with OAuth error params |
| User not authorized | `access_denied` | Redirect to `redirect_uri` with OAuth error params |
| User not logged in | `login_required` | Redirect to `redirect_uri` with OAuth error params |
| Invalid `redirect_uri` | `invalid_request_uri` | Render local error page |
| Internal signing/config error | `server_error` or `temporarily_unavailable` | Render local error page |

For redirectable errors, the library appends `error`, `error_description`, and
`state` when available. For non-redirectable errors, `render_error_page()` is used.

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

    def get_redirect(self, url):
        """
        This will be invoked when launch validation fails with a redirectable
        OAuth/OIDC error.
        """
        return HttpResponseRedirect(url)

    def render_error_page(self, message, status_code):
        """
        This will be invoked when launch validation fails with a local-only
        error such as `invalid_request_uri` or `server_error`.
        """
        return HttpResponse(message, status=status_code)

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
    message_launch = LTI1p3MessageLaunch(request, platform)

    return message_launch.lti_launch(*args, **kwargs)
```

### Launch error response behavior

`lti_launch()` uses the same policy as OIDC login:

- Redirect to the supplied `redirect_uri` for redirectable OAuth/OIDC errors such as `invalid_request`, `unauthorized_client`, `unsupported_response_type`, `invalid_scope`, `access_denied`, and `login_required`.
- Render a local error page for non-redirectable or server-side failures such as `invalid_request_uri`, `server_error`, and `temporarily_unavailable`.

## LTI Advantage Services

LTI Advantage extends the base launch with three optional services. Use
`LTIAdvantageMessageLaunchAbstract` instead of `MessageLaunchAbstract` to gain
access to them. All three methods return `self` so they can be chained.

```python
from lti1p3platform.message_launch import LTIAdvantageMessageLaunchAbstract

class LTI1p3MessageLaunch(LTIAdvantageMessageLaunchAbstract):
    # same abstract method implementations as MessageLaunchAbstract …
    pass
```

### Deep Linking (`set_dl`)

[LTI Deep Linking 2.0](https://www.imsglobal.org/spec/lti-dl/v2p0/) lets an
instructor pick content items inside the tool and return them to the platform.
When `set_dl` is called the launch message type is changed to
`LtiDeepLinkingRequest` and the platform's deep-link return URL is used as the
target instead of the normal resource-link launch URL.

```python
message_launch.set_dl(
    deep_link_return_url="https://platform.example.com/lti/deeplink/return",
    title="Select content",
    description="Choose a resource to embed",
    accept_multiple=True,          # allow selecting more than one item
    auto_create=True,              # platform auto-creates items without extra confirmation
    accept_types={"ltiResourceLink", "link", "file"},
    accept_presentation_document_targets={"iframe", "window"},
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `deep_link_return_url` | `str` | — | Platform URL the tool POSTs selected items back to. |
| `title` | `str` | `""` | Human-readable title for the request. |
| `description` | `str` | `""` | Human-readable description. |
| `accept_multiple` | `bool` | `False` | Whether the tool may return multiple items. |
| `auto_create` | `bool` | `True` | Whether the platform should auto-create items. |
| `accept_types` | `set[str] \| None` | `None` (all) | Allowed content-item types. |
| `extra_data` | `dict \| None` | `None` | Additional platform-defined data. |
| `accept_presentation_document_targets` | `set[str] \| None` | `None` (all) | Allowed document targets. |

### Assignments and Grades Service (`set_ags`)

[LTI AGS 2.0](https://www.imsglobal.org/spec/lti-ags/v2p0/) allows the tool to
read and write grades back to the platform gradebook.

```python
message_launch.set_ags(
    lineitems_url="https://platform.example.com/lti/lineitems/",
    lineitem_url="https://platform.example.com/lti/lineitems/42",  # optional
    allow_creating_lineitems=True,
    results_service_enabled=True,
    scores_service_enabled=True,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `lineitems_url` | `str` | — | Platform endpoint for the line-items container. |
| `lineitem_url` | `str \| None` | `None` | Endpoint for a single, pre-existing line item. |
| `allow_creating_lineitems` | `bool` | `True` | Whether the tool may create new line items. |
| `results_service_enabled` | `bool` | `True` | Whether the Results service is advertised. |
| `scores_service_enabled` | `bool` | `True` | Whether the Scores service is advertised. |

### Names and Role Provisioning Service (`set_nrps`)

[LTI NRPS 2.0](https://www.imsglobal.org/spec/lti-nrps/v2p0/) lets the tool
retrieve the enrollment roster for the current context (names, roles, and LIS
person source-dids).

```python
message_launch.set_nrps(
    context_memberships_url="https://platform.example.com/lti/memberships/",
)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `context_memberships_url` | `str` | Platform endpoint the tool calls to fetch the membership list. |

### Combining all three services

All three `set_*` methods return `self`, so they can be chained together:

```python
def lti_advantage_launch(request, *args, **kwargs):
    platform = get_registered_platform(*args, **kwargs)
    message_launch = LTI1p3MessageLaunch(request, platform)

    message_launch \
        .set_dl(
            deep_link_return_url="https://platform.example.com/lti/deeplink/return",
        ) \
        .set_ags(
            lineitems_url="https://platform.example.com/lti/lineitems/",
        ) \
        .set_nrps(
            context_memberships_url="https://platform.example.com/lti/memberships/",
        )

    return message_launch.lti_launch(*args, **kwargs)
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
