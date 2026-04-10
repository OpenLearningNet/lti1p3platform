import typing as t

import pytest

# pylint: disable=protected-access

from lti1p3platform.exceptions import (
    InvalidRequestData,
    InvalidRequestUri,
    InvalidScopeException,
    PlatformNotReadyException,
    InternalSigningError,
    UnauthorizedClient,
    UnsupportedResponseType,
)
from lti1p3platform.message_launch import MessageLaunchAbstract
from lti1p3platform.oidc_login import OIDCLoginAbstract
from lti1p3platform.request import Request

from .platform_config import PLATFORM_CONFIG, PlatformConf


class _DummyRequest(Request):
    def build_metadata(self, request: t.Any) -> t.Dict[str, t.Any]:
        return request


class _DummyMessageLaunch(MessageLaunchAbstract):
    def render_launch_form(
        self, launch_data: t.Dict[str, t.Any], **kwargs: t.Any
    ) -> t.Any:
        return launch_data

    def get_redirect(self, url: str) -> t.Any:
        return {"type": "redirect", "url": url}

    def render_error_page(self, message: str, status_code: int) -> t.Any:
        return {"type": "error_page", "message": message, "status_code": status_code}


class _DummyOIDCLogin(OIDCLoginAbstract):
    def set_lti_message_hint(self, **kwargs: t.Any) -> None:
        self._lti_message_hint = kwargs.get("message_hint")

    def get_redirect(self, url: str) -> t.Any:
        return {"type": "redirect", "url": url}

    def render_error_page(self, message: str, status_code: int) -> t.Any:
        return {"type": "error_page", "message": message, "status_code": status_code}


def _make_message_launch() -> _DummyMessageLaunch:
    request = _DummyRequest(
        {
            "method": "POST",
            "form_data": {},
            "get_data": {},
            "headers": {},
            "content_type": None,
            "path": "/launch",
            "json": None,
        }
    )
    platform = PlatformConf()
    registration = platform.get_registration()
    registration.set_tool_redirect_uris(
        [
            PLATFORM_CONFIG["launch_url"],
            PLATFORM_CONFIG["deeplink_launch_url"],
        ]
    )

    launch = _DummyMessageLaunch(request, platform)
    launch._registration = registration
    return launch


def _make_oidc_login() -> _DummyOIDCLogin:
    request = _DummyRequest(
        {
            "method": "GET",
            "form_data": {},
            "get_data": {},
            "headers": {},
            "content_type": None,
            "path": "/oidc",
            "json": None,
        }
    )
    login = _DummyOIDCLogin(request, PlatformConf())
    login.set_lti_message_hint(message_hint="resource-link-123")
    return login


def test_validate_preflight_response_missing_client_id_raises_invalid_request():
    launch = _make_message_launch()

    with pytest.raises(InvalidRequestData, match="client_id"):
        launch.validate_preflight_response(
            {
                "response_type": "id_token",
                "scope": "openid",
                "nonce": "nonce-123",
                "state": "state-123",
                "redirect_uri": PLATFORM_CONFIG["launch_url"],
            }
        )


def test_validate_preflight_response_unknown_client_id_raises_unauthorized_client():
    launch = _make_message_launch()

    with pytest.raises(UnauthorizedClient, match="client_id"):
        launch.validate_preflight_response(
            {
                "client_id": "wrong-client",
                "response_type": "id_token",
                "scope": "openid",
                "nonce": "nonce-123",
                "state": "state-123",
                "redirect_uri": PLATFORM_CONFIG["launch_url"],
            }
        )


def test_validate_preflight_response_wrong_response_type_raises_unsupported_response_type():
    launch = _make_message_launch()

    with pytest.raises(UnsupportedResponseType, match="response_type"):
        launch.validate_preflight_response(
            {
                "client_id": PLATFORM_CONFIG["client_id"],
                "response_type": "code",
                "scope": "openid",
                "nonce": "nonce-123",
                "state": "state-123",
                "redirect_uri": PLATFORM_CONFIG["launch_url"],
            }
        )


def test_validate_preflight_response_wrong_scope_raises_invalid_scope():
    launch = _make_message_launch()

    with pytest.raises(InvalidScopeException, match="scope"):
        launch.validate_preflight_response(
            {
                "client_id": PLATFORM_CONFIG["client_id"],
                "response_type": "id_token",
                "scope": "profile",
                "nonce": "nonce-123",
                "state": "state-123",
                "redirect_uri": PLATFORM_CONFIG["launch_url"],
            }
        )


def test_validate_preflight_response_invalid_redirect_uri_raises_invalid_request_uri():
    launch = _make_message_launch()

    with pytest.raises(InvalidRequestUri, match="redirect_uri"):
        launch.validate_preflight_response(
            {
                "client_id": PLATFORM_CONFIG["client_id"],
                "response_type": "id_token",
                "scope": "openid",
                "nonce": "nonce-123",
                "state": "state-123",
                "redirect_uri": "https://evil.example.com/callback",
            }
        )


def test_prepare_preflight_url_missing_message_hint_raises_platform_not_ready():
    login = _make_oidc_login()
    login._lti_message_hint = None

    with pytest.raises(PlatformNotReadyException, match="lti_message_hint"):
        login.prepare_preflight_url("user-123")


def test_prepare_preflight_url_missing_oidc_login_url_raises_platform_not_ready():
    login = _make_oidc_login()
    login._registration.set_oidc_login_url(None)

    with pytest.raises(PlatformNotReadyException, match="OIDC login URL"):
        login.prepare_preflight_url("user-123")


def test_get_error_response_redirects_redirectable_oauth_errors():
    launch = _make_message_launch()

    response = launch.get_error_response(
        InvalidScopeException("Invalid scope"),
        redirect_uri=PLATFORM_CONFIG["launch_url"],
        state="state-123",
    )

    assert response["type"] == "redirect"
    assert "error=invalid_scope" in response["url"]
    assert "state=state-123" in response["url"]


def test_get_error_response_renders_page_for_non_redirectable_errors():
    launch = _make_message_launch()

    response = launch.get_error_response(
        InvalidRequestUri("Bad redirect URI"),
        redirect_uri=PLATFORM_CONFIG["launch_url"],
    )

    assert response["type"] == "error_page"
    assert response["status_code"] == 400


def test_lti_launch_redirects_when_validation_error_is_redirectable():
    request = _DummyRequest(
        {
            "method": "POST",
            "form_data": {
                "client_id": PLATFORM_CONFIG["client_id"],
                "response_type": "id_token",
                "scope": "profile",
                "nonce": "nonce-123",
                "state": "state-123",
                "redirect_uri": PLATFORM_CONFIG["launch_url"],
            },
            "get_data": {},
            "headers": {},
            "content_type": None,
            "path": "/launch",
            "json": None,
        }
    )
    platform = PlatformConf()
    platform.get_registration().set_tool_redirect_uris([PLATFORM_CONFIG["launch_url"]])
    launch = _DummyMessageLaunch(request, platform)

    response = launch.lti_launch()

    assert response["type"] == "redirect"
    assert "error=invalid_scope" in response["url"]


def test_lti_launch_renders_page_when_validation_error_is_not_redirectable():
    request = _DummyRequest(
        {
            "method": "POST",
            "form_data": {
                "client_id": PLATFORM_CONFIG["client_id"],
                "response_type": "id_token",
                "scope": "openid",
                "nonce": "nonce-123",
                "state": "state-123",
                "redirect_uri": "https://evil.example.com/callback",
            },
            "get_data": {},
            "headers": {},
            "content_type": None,
            "path": "/launch",
            "json": None,
        }
    )
    platform = PlatformConf()
    platform.get_registration().set_tool_redirect_uris([PLATFORM_CONFIG["launch_url"]])
    launch = _DummyMessageLaunch(request, platform)

    response = launch.lti_launch()

    assert response["type"] == "error_page"
    assert response["status_code"] == 400


def test_initiate_login_renders_page_for_internal_server_errors():
    login = _make_oidc_login()
    login._registration.set_platform_private_key(None)

    response = login.get_error_response(InternalSigningError("Signing failed"))

    assert response["type"] == "error_page"
    assert response["status_code"] == 500


def test_get_error_response_maps_value_error_to_invalid_request_status_code():
    launch = _make_message_launch()

    response = launch.get_error_response(ValueError("bad input"))

    assert response["type"] == "error_page"
    assert response["status_code"] == 400


def test_get_error_response_redirects_value_error_as_invalid_request():
    launch = _make_message_launch()

    response = launch.get_error_response(
        ValueError("bad input"),
        redirect_uri=PLATFORM_CONFIG["launch_url"],
        state="state-123",
    )

    assert response["type"] == "redirect"
    assert "error=invalid_request" in response["url"]
