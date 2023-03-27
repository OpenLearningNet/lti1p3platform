"""
LTI Deep Linking service implementation
"""
import typing as t
from .constants import LTI_DEEP_LINKING_ACCEPTED_TYPES
from .exceptions import LtiDeepLinkingContentTypeNotSupported


# pylint: disable=too-few-public-methods
class LtiDeepLinking:
    """
    LTI Advantage - Deep Linking Service

    Reference:
    http://www.imsglobal.org/spec/lti-dl/v2p0#file
    """

    def __init__(
        self,
        deep_linking_return_url: str,
    ) -> None:
        """
        Class initialization.
        """
        self.deep_linking_return_url = deep_linking_return_url

    def get_lti_deep_linking_launch_claim(
        self,
        title: str = "",
        description: str = "",
        accept_types: t.Optional[t.Set[str]] = None,
        extra_data: t.Optional[t.Dict[str, t.Any]] = None,
    ) -> t.Dict[str, t.Any]:
        """
        Returns LTI Deep Linking Claim to be injected in the LTI launch message.
        """
        if not accept_types:
            accept_types = LTI_DEEP_LINKING_ACCEPTED_TYPES

        # Check if required types are accepted, if not throw
        accept_types_claim = []
        for content_type in accept_types:
            if content_type in LTI_DEEP_LINKING_ACCEPTED_TYPES:
                accept_types_claim.append(content_type)
            else:
                raise LtiDeepLinkingContentTypeNotSupported

        # Consctruct Deep Linking Claim
        deep_linking_claim = {
            "accept_types": accept_types_claim,
            "accept_presentation_document_targets": ["iframe", "window", "embed"],
            # Accept multiple items on from Deep Linking responses.
            "accept_multiple": True,
            # Automatically saves Content Items without asking to user
            "auto_create": True,
            # Other parameters
            "title": title,
            "text": description,
            "deep_link_return_url": self.deep_linking_return_url,
        }

        # Extra data is an optional parameter that can be sent.
        # It's opaque to the tool, but WILL be sent back in the
        # deep link response.
        if extra_data:
            deep_linking_claim.update(
                {
                    "data": extra_data,
                }
            )

        return {
            "https://purl.imsglobal.org/spec/lti-dl/claim/deep_linking_settings": deep_linking_claim
        }
