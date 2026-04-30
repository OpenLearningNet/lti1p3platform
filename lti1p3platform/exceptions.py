from lti1p3platform import error_codes


REDIRECT_ERROR_CODES = {
    error_codes.INVALID_REQUEST,
    error_codes.UNAUTHORIZED_CLIENT,
    error_codes.ACCESS_DENIED,
    error_codes.UNSUPPORTED_RESPONSE_TYPE,
    error_codes.INVALID_SCOPE,
    error_codes.LOGIN_REQUIRED,
    error_codes.INTERACTION_REQUIRED,
    error_codes.ACCOUNT_SELECTION_REQUIRED,
    error_codes.CONSENT_REQUIRED,
}


ERROR_PAGE_STATUS_CODES = {
    error_codes.INVALID_REQUEST: 400,
    error_codes.UNAUTHORIZED_CLIENT: 400,
    error_codes.ACCESS_DENIED: 403,
    error_codes.UNSUPPORTED_RESPONSE_TYPE: 400,
    error_codes.INVALID_SCOPE: 400,
    error_codes.INVALID_CLIENT: 401,
    error_codes.INVALID_GRANT: 400,
    error_codes.UNSUPPORTED_GRANT_TYPE: 400,
    error_codes.INVALID_TOKEN: 401,
    error_codes.INSUFFICIENT_SCOPE: 403,
    error_codes.INTERACTION_REQUIRED: 400,
    error_codes.LOGIN_REQUIRED: 401,
    error_codes.ACCOUNT_SELECTION_REQUIRED: 400,
    error_codes.CONSENT_REQUIRED: 400,
    error_codes.INVALID_REQUEST_URI: 400,
    error_codes.INVALID_REQUEST_OBJECT: 400,
    error_codes.REQUEST_NOT_SUPPORTED: 400,
    error_codes.REQUEST_URI_NOT_SUPPORTED: 400,
    error_codes.REGISTRATION_NOT_SUPPORTED: 400,
    error_codes.SERVER_ERROR: 500,
    error_codes.TEMPORARILY_UNAVAILABLE: 503,
}


def get_error_code(error: object) -> str:
    if isinstance(error, str):
        return error

    if isinstance(error, (ValueError, TypeError)):
        return error_codes.INVALID_REQUEST

    code = getattr(error, "code", None)
    if isinstance(code, str):
        return code

    return error_codes.SERVER_ERROR


def get_error_response_behavior(error: object) -> str:
    code = get_error_code(error)
    if code in REDIRECT_ERROR_CODES:
        return "redirect"
    return "error_page"


def get_error_page_status_code(error: object) -> int:
    code = get_error_code(error)
    return ERROR_PAGE_STATUS_CODES.get(code, 500)


class PreflightRequestValidationException(Exception):
    code = error_codes.INVALID_REQUEST


class LtiDeepLinkingContentTypeNotSupported(Exception):
    code = error_codes.INVALID_REQUEST


class MissingRequiredClaim(Exception):
    code = error_codes.INVALID_REQUEST


class UnsupportedGrantType(Exception):
    code = error_codes.UNSUPPORTED_GRANT_TYPE


class UnsupportedResponseType(Exception):
    code = error_codes.UNSUPPORTED_RESPONSE_TYPE


class UnauthorizedClient(Exception):
    """Canonical exception name kept for API compatibility."""

    code = error_codes.UNAUTHORIZED_CLIENT


class InvalidKeySetUrl(Exception):
    code = error_codes.INVALID_REQUEST_URI


class InvalidRequestUri(Exception):
    code = error_codes.INVALID_REQUEST_URI


class LtiException(Exception):
    code = error_codes.SERVER_ERROR


class LtiDeepLinkingResponseException(Exception):
    code = error_codes.INVALID_REQUEST


class InvalidJwtToken(Exception):
    code = error_codes.INVALID_TOKEN


class InvalidClientAssertion(Exception):
    code = error_codes.INVALID_CLIENT


class PlatformNotReadyException(Exception):
    """
    Raised when platform is not yet initialized/configured.
    Per OAuth 2.0 RFC 6749 §5.2: server is unable to handle request due to
    temporary overloading or maintenance.
    """

    code = error_codes.TEMPORARILY_UNAVAILABLE


class InvalidRequestData(Exception):
    """
    Raised when request data is missing required fields or contains invalid values.
    Per OAuth 2.0 RFC 6749 §4.1.2.1: request is missing required parameter,
    includes invalid parameter, or is otherwise malformed.
    """

    code = error_codes.INVALID_REQUEST


class InvalidScopeException(Exception):
    """
    Raised when requested scope is invalid, unknown, or malformed.
    Per OAuth 2.0 RFC 6749 §4.1.2.1: scope parameter validation failure.
    """

    code = error_codes.INVALID_SCOPE


class AccessDeniedException(Exception):
    code = error_codes.ACCESS_DENIED


class LoginRequiredException(Exception):
    code = error_codes.LOGIN_REQUIRED


class InternalSigningError(Exception):
    code = error_codes.SERVER_ERROR


class LtiServiceException(Exception):
    code = error_codes.SERVER_ERROR

    def __init__(self, message: str, status_code: int) -> None:
        super().__init__(message)

        self.status_code = status_code
        self.message = message


class LineItemNotFoundException(LtiException):
    code = error_codes.INVALID_REQUEST
