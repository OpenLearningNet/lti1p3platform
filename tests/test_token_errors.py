"""Tests for RFC 6749 §5.2 token endpoint error responses."""
import pytest

from lti1p3platform.exceptions import (
    InvalidClientAssertion,
    InvalidJwtToken,
    LtiException,
    MissingRequiredClaim,
    PlatformNotReadyException,
    UnsupportedGrantType,
)
from lti1p3platform.token_errors import get_access_token_error_response


@pytest.mark.parametrize(
    "error, code, status",
    [
        (MissingRequiredClaim("scope missing"), "invalid_request", 400),
        (UnsupportedGrantType(), "unsupported_grant_type", 400),
        (InvalidClientAssertion("Invalid client_assertion"), "invalid_client", 401),
        ("invalid_scope", "invalid_scope", 400),
        (PlatformNotReadyException("no key"), "server_error", 500),
        (InvalidJwtToken("bad"), "server_error", 500),
        (RuntimeError("boom"), "server_error", 500),
    ],
)
def test_access_token_error_response_maps_code_and_status(error, code, status):
    resp = get_access_token_error_response(error)
    assert resp.code == status
    assert resp.result["error"] == code
    assert resp.media_type == "application/json"
    assert resp.headers == {"Cache-Control": "no-store", "Pragma": "no-cache"}


def test_access_token_error_response_hides_exception_message():
    resp = get_access_token_error_response(
        LtiException("Error during fetch URL https://internal.example.com/jwks")
    )
    assert "internal.example.com" not in resp.result["error_description"]
    assert resp.result["error_description"] == resp.message


def test_access_token_error_response_custom_description():
    resp = get_access_token_error_response(
        PlatformNotReadyException(), description="Try again later. Ref ABC123"
    )
    assert resp.result == {
        "error": "server_error",
        "error_description": "Try again later. Ref ABC123",
    }
