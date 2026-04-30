# OAuth 2.0 and OpenID Connect Error Codes
# Sources:
#   - OAuth 2.0 RFC 6749 §4.1.2.1 (Authorization Endpoint errors)
#   - OAuth 2.0 RFC 6749 §5.2 (Token Endpoint errors)
#   - OAuth 2.0 Bearer Token Usage RFC 6750 §3 (Resource Server errors)
#   - OpenID Connect Core 1.0 §3.1.2.6 and §18.3.1 (IANA OAuth Extensions Error Registry)
#   https://openid.net/specs/openid-connect-core-1_0.html#OAuthErrorRegistry

# ---------------------------------------------------------------------------
# OAuth 2.0 RFC 6749 – Authorization Endpoint errors (§4.1.2.1)
# ---------------------------------------------------------------------------

# The request is missing a required parameter, includes an invalid parameter
# value, includes a parameter more than once, or is otherwise malformed.
INVALID_REQUEST = "invalid_request"

# The client is not authorized to request an authorization code using this
# method.
UNAUTHORIZED_CLIENT = "unauthorized_client"

# The resource owner or authorization server denied the request.
ACCESS_DENIED = "access_denied"

# The authorization server does not support obtaining an authorization code
# using this method.
UNSUPPORTED_RESPONSE_TYPE = "unsupported_response_type"

# The requested scope is invalid, unknown, or malformed.
INVALID_SCOPE = "invalid_scope"

# The authorization server encountered an unexpected condition that prevented
# it from fulfilling the request.
SERVER_ERROR = "server_error"

# The authorization server is currently unable to handle the request due to a
# temporary overloading or maintenance of the server.
TEMPORARILY_UNAVAILABLE = "temporarily_unavailable"

# ---------------------------------------------------------------------------
# OAuth 2.0 RFC 6749 – Token Endpoint errors (§5.2)
# ---------------------------------------------------------------------------

# Client authentication failed (e.g., unknown client, no client authentication
# included, or unsupported authentication method).
INVALID_CLIENT = "invalid_client"

# The provided authorization grant (e.g., authorization code, resource owner
# credentials) or refresh token is invalid, expired, revoked, does not match
# the redirection URI used in the authorization request, or was issued to
# another client.
INVALID_GRANT = "invalid_grant"

# The authorization grant type is not supported by the authorization server.
UNSUPPORTED_GRANT_TYPE = "unsupported_grant_type"

# ---------------------------------------------------------------------------
# OAuth 2.0 Bearer Token Usage RFC 6750 – Resource Server / UserInfo errors (§3)
# ---------------------------------------------------------------------------

# The access token provided is expired, revoked, malformed, or invalid for
# other reasons.
INVALID_TOKEN = "invalid_token"

# The request requires higher privileges than provided by the access token.
INSUFFICIENT_SCOPE = "insufficient_scope"

# ---------------------------------------------------------------------------
# OpenID Connect Core 1.0 – IANA OAuth Extensions Error Registry (§18.3.1)
# Used in Authentication Error Responses (§3.1.2.6)
# ---------------------------------------------------------------------------

# The Authorization Server requires End-User interaction of some form to
# proceed. Returned when prompt=none but interaction is required.
INTERACTION_REQUIRED = "interaction_required"

# The Authorization Server requires End-User authentication. Returned when
# prompt=none but the End-User is not authenticated.
LOGIN_REQUIRED = "login_required"

# The End-User is required to select a session at the Authorization Server.
# Returned when prompt=none but account selection is required.
ACCOUNT_SELECTION_REQUIRED = "account_selection_required"

# The Authorization Server requires End-User consent. Returned when
# prompt=none but consent has not been given.
CONSENT_REQUIRED = "consent_required"

# The request_uri in the Authorization Request returns an error or contains
# invalid data.
INVALID_REQUEST_URI = "invalid_request_uri"

# The request parameter contains an invalid Request Object.
INVALID_REQUEST_OBJECT = "invalid_request_object"

# The OP does not support use of the request parameter defined in §6.
REQUEST_NOT_SUPPORTED = "request_not_supported"

# The OP does not support use of the request_uri parameter defined in §6.
REQUEST_URI_NOT_SUPPORTED = "request_uri_not_supported"

# The OP does not support use of the registration parameter defined in §7.2.1.
REGISTRATION_NOT_SUPPORTED = "registration_not_supported"
