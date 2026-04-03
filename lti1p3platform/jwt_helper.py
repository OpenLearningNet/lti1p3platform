"""
JWT (JSON Web Token) Encoding Utilities for LTI 1.3

What is JWT?
============
JWT (JSON Web Token) is a standard format for securely transmitting claims between parties.
All LTI 1.3 messages are signed JWTs.

JWT Structure:
- Header: Specifies algorithm and key ID
- Payload: The actual data/claims
- Signature: Generated using private key, verified with public key

Example JWT:
eyJhbGciOiJSUzI1NiIsImtpZCI6IjEifQ.eyJpc3MiOiJodHRwczovL3BsYXRmb3JtLnRydWN1dC5jb20ifQ.signature...

Three parts separated by dots (base64url-encoded):
1. Header: eyJhbGciOiJSUzI1NiIsImtpZCI6IjEifQ
   Decoded: {"alg":"RS256","kid":"1"}
   
2. Payload: eyJpc3MiOiJodHRwczovL3BsYXRmb3JtLnRydWN1dC5jb20ifQ
   Decoded: {"iss":"https://platform.trucut.com"}
   
3. Signature: signature... (cryptographic signature)

LTI 1.3 JWT Requirements:
========================
- Algorithm: RS256 (RSA with SHA-256)
- Key: Platform's private key for signing
- Payload: Contains claims about user/context

Common JWT Claims:
- iss (issuer): Who created the token
- sub (subject): Who the token is about
- aud (audience): Who should validate this token
- iat (issued at): When the token was created
- exp (expiration): When the token expires
- nonce: Random value for replay protection
- jti: Unique token ID for replay protection

Security:
- Signature proves token wasn't tampered with
- Signature proves it came from who claims to have created it
- Can be validated offline without contacting issuer
- No secrets transmitted (only public key needed to verify)

Reference: https://tools.ietf.org/html/rfc7519
"""
import typing as t
import jwt


def jwt_encode(
    payload: t.Mapping[str, t.Any],
    key: str,
    algorithm: str = "HS256",
    headers: t.Optional[t.Mapping[str, t.Any]] = None,
    json_encoder: t.Optional[t.Callable[(...), t.Any]] = None,
) -> str:
    """
    Encode a JWT token with the given payload and key
    
    PyJWT Wrapper: Handles compatibility between PyJWT versions
    - PyJWT 2.0.0+: Returns string (UTF-8 encoded)
    - PyJWT < 2.0.0: Returns bytes
    - This function always returns a string for consistency
    
    LTI 1.3 JWT Encoding Process:
    1. Create payload dict with all necessary claims
    2. Call this function with payload and platform's private key
    3. PyJWT creates signature using RS256 algorithm
    4. Returns signed JWT string (three dot-separated base64url-encoded parts)
    5. Platform sends this JWT to tool (usually as parameter in redirect)
    
    JWT Payload Example (LTI Launch Message):
    {
        "iss": "https://platform.trucut.com",
        "sub": "user-123",
        "aud": "https://tool.example.com",
        "iat": 1634567890,
        "exp": 1634567950,
        "nonce": "random-nonce-xyz",
        "https://purl.imsglobal.org/spec/lti/claim/deployment_id": "deployment-456",
        "https://purl.imsglobal.org/spec/lti/claim/user_id": "user-123",
        ...
    }
    
    Parameters:
        payload: Dictionary of claims to include in JWT
        key: Private key in PEM format (string)
        algorithm: Signing algorithm (default HS256, LTI uses RS256)
                  - HS256: HMAC with SHA-256 (symmetric, shared secret)
                  - RS256: RSA with SHA-256 (asymmetric, public/private key)
                  - LTI 1.3 uses RS256 for security
        headers: Additional JWT headers (e.g., key ID 'kid' for key rotation)
        json_encoder: Custom JSON encoder if needed
    
    Returns:
        str: The encoded JWT token (three dot-separated parts)
    
    Example Use:
    >>> payload = {
    ...     "iss": "https://platform.com",
    ...     "sub": "user-123",
    ...     "aud": "https://tool.com",
    ...     "iat": 1634567890,
    ...     "exp": 1634567950
    ... }
    >>> token = jwt_encode(payload, private_key_pem, "RS256")
    >>> # token = "eyJ0eXAiOiJKV1QiLCJhbGc..."
    
    Reference:
    - JWT Format: https://tools.ietf.org/html/rfc7519#section-3
    - RS256 Algorithm: https://tools.ietf.org/html/rfc7518#section-3.3
    - LTI JWT Encoding: https://www.imsglobal.org/spec/lti/v1p3/#jwt-message-claims
    """
    encoded_jwt = jwt.encode(payload, key, algorithm, headers, json_encoder)

    if isinstance(encoded_jwt, bytes):
        encoded_jwt = encoded_jwt.decode("utf-8")  # type: ignore

    return encoded_jwt  # type: ignore
