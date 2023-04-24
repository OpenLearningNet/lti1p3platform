class PreflightRequestValidationException(Exception):
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


class LtiDeepLinkingResponseException(Exception):
    pass


class LtiServiceException(Exception):
    def __init__(self, message: str, status_code: int) -> None:
        super().__init__(message)

        self.status_code = status_code
        self.message = message


class LineItemNotFoundException(LtiException):
    pass
