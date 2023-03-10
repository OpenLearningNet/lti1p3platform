
class PreflightRequestValidationException(Exception):
    """Preflight request validation exception"""
    pass

class LtiDeepLinkingContentTypeNotSupported(Exception):
    pass

class MissingRequiredClaim(Exception):
    pass

class UnsupportedGrantType(Exception):
    pass

class InvalidKeySetUrl(Exception):
    pass

class LtiException(Exception):
    pass
