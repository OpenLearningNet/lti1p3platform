"""
Error responses for the OAuth 2.0 access token endpoint.

LTI 1.3 services get access tokens with the OAuth 2.0 client credentials
grant and a JWT client assertion (1EdTech Security Framework, RFC 7523).
A rejected token request must use the error format in RFC 6749 §5.2.
"""
import typing as t

from . import error_codes
from .exceptions import get_error_code
from .response import Response

# RFC 6749 §5.2 error codes, with fixed descriptions. The descriptions never
# include exception messages, because those can hold URLs or tool responses.
TOKEN_ENDPOINT_ERROR_DESCRIPTIONS = {
    error_codes.INVALID_REQUEST: (
        "The token request is missing a required parameter or is malformed."
    ),
    error_codes.INVALID_CLIENT: "Client authentication failed.",
    error_codes.INVALID_GRANT: "The authorization grant is invalid.",
    error_codes.UNAUTHORIZED_CLIENT: (
        "The client is not authorized to use this grant type."
    ),
    error_codes.UNSUPPORTED_GRANT_TYPE: "The grant type is not supported.",
    error_codes.INVALID_SCOPE: "The requested scope is invalid.",
}

SERVER_ERROR_DESCRIPTION = "The token request could not be processed."

TOKEN_ENDPOINT_ERROR_HEADERS = {
    "Cache-Control": "no-store",
    "Pragma": "no-cache",
}


def get_access_token_error_response(
    error: object, description: t.Optional[str] = None
) -> Response:
    """
    Build an RFC 6749 §5.2 error response for a rejected token request.

    Parameters:
        error: An exception raised by `get_access_token`, or an error code
        description: Optional text to use instead of the default description

    Returns:
        Response: JSON body with `error` and `error_description`, status 401
        for `invalid_client`, 400 for other §5.2 codes and 500 for anything
        else (reported as `server_error`), and `no-store` cache headers.
    """
    code = get_error_code(error)

    if code == error_codes.INVALID_CLIENT:
        status = 401
    elif code in TOKEN_ENDPOINT_ERROR_DESCRIPTIONS:
        status = 400
    else:
        code = error_codes.SERVER_ERROR
        status = 500

    error_description = description or TOKEN_ENDPOINT_ERROR_DESCRIPTIONS.get(
        code, SERVER_ERROR_DESCRIPTION
    )

    return Response(
        {"error": code, "error_description": error_description},
        status,
        error_description,
        headers=dict(TOKEN_ENDPOINT_ERROR_HEADERS),
    )
